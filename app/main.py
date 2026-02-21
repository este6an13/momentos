import os
import re
from typing import Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, Depends, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import shutil
import json
import uuid
from PIL import Image, ExifTags
from sqlalchemy.orm import Session
from sqlalchemy import or_
from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local").lower()
GCP_BUCKET_NAME = os.environ.get("GCP_BUCKET_NAME")
CDN_DOMAIN = os.environ.get("CDN_DOMAIN")

if STORAGE_BACKEND == "gcp" and not GCP_BUCKET_NAME:
    print("WARNING: STORAGE_BACKEND is gcp but GCP_BUCKET_NAME is not set.")

def get_gcp_bucket():
    if not GCP_BUCKET_NAME:
        return None
    client = storage.Client()
    return client.bucket(GCP_BUCKET_NAME)

from .database import get_db, init_db
from .models import Photo

app = FastAPI(title="Photo Gallery")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Register global template function for generating image URLs
def get_image_url(filename: str) -> str:
    if STORAGE_BACKEND == "gcp" and GCP_BUCKET_NAME:
        if CDN_DOMAIN:
            # If Cloudflare is fronting the bucket directly
            return f"https://{CDN_DOMAIN}/{filename}"
        # Fallback to direct GCP Bucket URL for local testing without CDN
        return f"https://storage.googleapis.com/{GCP_BUCKET_NAME}/{filename}"
    return f"/static/images/{filename}"

templates.env.globals["get_image_url"] = get_image_url

IMAGES_DIR = Path("static/images")
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".JPG", ".JPEG", ".PNG", ".WEBP"}


def _filename_to_title(filename: str) -> str:
    """Convert a filename like 'my_photo_2024.jpg' to 'My Photo 2024'"""
    stem = Path(filename).stem
    # Replace underscores/hyphens/dots with spaces, then title-case
    title = re.sub(r"[_\-\.]+", " ", stem).strip().title()
    return title or filename


def scan_photos_folder(db: Session):
    """Scan static/images/ and sync with database. Disabled in GCP mode."""
    if STORAGE_BACKEND == "gcp":
        # In GCP mode, the DB is the source of truth; we don't scan the bucket.
        return

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Get all image files on disk
    disk_files = {
        f.name
        for f in IMAGES_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in {ext.lower() for ext in SUPPORTED_EXTENSIONS}
    }

    # Get all filenames currently in DB
    db_photos = {p.filename: p for p in db.query(Photo).all()}

    # Add new files not yet in DB
    added: int = 0
    for filename in disk_files:
        if filename not in db_photos:
            photo = Photo(
                filename=filename,
                title=_filename_to_title(filename),
                uploaded_at=datetime.utcnow(),
            )
            db.add(photo)
            added += 1

    # Remove DB entries for files that no longer exist on disk
    removed: int = 0
    for filename, photo_to_delete in db_photos.items():
        if filename not in disk_files:
            db.delete(photo_to_delete)
            removed += 1

    db.commit()
    if added or removed:
        print(f"Photo sync: +{added} added, -{removed} removed")


@app.on_event("startup")
async def startup_event():
    init_db()
    db_gen = get_db()
    db = next(db_gen)
    try:
        scan_photos_folder(db)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main gallery page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/photos", response_class=HTMLResponse)
async def get_photos(request: Request, q: Optional[str] = None, db: Session = Depends(get_db)):
    """HTMX endpoint for photo grid — always syncs folder first"""
    scan_photos_folder(db)
    
    query = db.query(Photo)
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Photo.filename.ilike(search_term),
                Photo.title.ilike(search_term),
                Photo.description.ilike(search_term),
                Photo.location.ilike(search_term),
                Photo.tags.ilike(search_term)
            )
        )
        
    photos = query.order_by(Photo.uploaded_at.desc()).all()
    return templates.TemplateResponse("photo_grid.html", {
        "request": request,
        "photos": photos
    })


@app.get("/photo/{photo_id}", response_class=HTMLResponse)
async def get_photo_detail(photo_id: int, request: Request, db: Session = Depends(get_db)):
    """HTMX endpoint for photo details with prev/next navigation"""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        return HTMLResponse(content="Photo not found", status_code=404)

    # Get ordered list of all IDs (same order as grid: newest first)
    all_rows = db.query(Photo.id).order_by(Photo.uploaded_at.desc()).all()
    all_ids: list[int] = [int(row[0]) for row in all_rows]
    
    try:
        idx = all_ids.index(photo_id)
    except ValueError:
        idx = -1
        
    prev_id = all_ids[idx - 1] if idx > 0 else None
    next_id = all_ids[idx + 1] if idx >= 0 and idx < len(all_ids) - 1 else None

    return templates.TemplateResponse("photo_detail.html", {
        "request": request,
        "photo": photo,
        "prev_id": prev_id,
        "next_id": next_id,
    })


@app.post("/photos/scan", response_class=HTMLResponse)
async def rescan_photos(request: Request, db: Session = Depends(get_db)):
    """Manually re-trigger folder scan and refresh the grid"""
    scan_photos_folder(db)
    photos = db.query(Photo).order_by(Photo.uploaded_at.desc()).all()
    return templates.TemplateResponse("photo_grid.html", {
        "request": request,
        "photos": photos
    })

@app.get("/upload", response_class=HTMLResponse)
async def get_upload_page(request: Request):
    """Render the upload interface"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload")
async def handle_upload(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(""),
    description: str = Form(""),
    location: str = Form(""),
    taken_at: str = Form(""),
    tags: str = Form(""),
    db: Session = Depends(get_db)
):
    """Handle photo upload and metadata"""
    
    # Generate unique filename to prevent overwrites
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    if STORAGE_BACKEND == "gcp":
        # We need a local temp path for EXIF extraction
        temp_dir = Path("tmp")
        temp_dir.mkdir(exist_ok=True)
        file_path = temp_dir / unique_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Upload to GCP
        bucket = get_gcp_bucket()
        if bucket:
            blob = bucket.blob(unique_filename)
            blob.upload_from_filename(file_path)
    else:
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        file_path = IMAGES_DIR / unique_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
    # Extract EXIF wrapper
    exif_dict = {}
    try:
        with Image.open(file_path) as img:
            exif = img.getexif()
            if exif:
                for k, v in exif.items():
                    if k in ExifTags.TAGS:
                        val = v
                        if isinstance(val, bytes):
                            try:
                                val = val.decode('utf-8', errors='replace')
                            except Exception:
                                val = str(val)
                        exif_dict[ExifTags.TAGS[k]] = str(val)
                        
            # If datetime original is in EXIF and taken_at wasn't manually specified
            if not taken_at and "DateTimeOriginal" in exif_dict:
                try:
                    dt_str = exif_dict["DateTimeOriginal"]
                    parts = dt_str.split(' ')
                    date_str = parts[0].replace(':', '-')
                    taken_at = f"{date_str}T{parts[1]}"
                except Exception:
                    pass
    except Exception as e:
        print(f"Error extracting EXIF: {e}")
        
    # Clean up temp file if in GCP mode
    if STORAGE_BACKEND == "gcp" and file_path.exists():
        file_path.unlink()
        
    # Check if photo already exists in DB
    photo = db.query(Photo).filter(Photo.filename == unique_filename).first()
    
    parsed_taken_at = None
    if taken_at:
        try:
            parsed_taken_at = datetime.fromisoformat(taken_at)
        except ValueError:
            pass # ignore invalid dates for now
            
    if not photo:
        photo = Photo(
            filename=unique_filename,
            uploaded_at=datetime.utcnow()
        )
        db.add(photo)
    
    photo.title = title or _filename_to_title(file.filename)
    photo.description = description
    photo.location = location
    photo.taken_at = parsed_taken_at
    photo.exif_data = json.dumps(exif_dict) if exif_dict else None
    
    # process tags
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        photo.set_tags(tag_list)
        
    db.commit()
    
    return {"message": "success"}

