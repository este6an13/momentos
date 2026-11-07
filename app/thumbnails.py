"""Small WebP copies of photos, used by the grid and album covers."""
from pathlib import Path

from PIL import Image, ImageOps

THUMB_DIR = "thumbs"
THUMB_WIDTH = 800
THUMB_MAX_HEIGHT = 2400  # keeps very tall photos from staying huge
THUMB_QUALITY = 78
THUMB_CACHE_CONTROL = "public, max-age=31536000"


def thumb_path(filename: str) -> str:
    """Path of a photo's thumbnail, relative to the image base URL or folder."""
    return f"{THUMB_DIR}/{filename}.webp"


def make_thumbnail(source: Path, dest: Path) -> None:
    """Write a resized WebP copy of `source` to `dest`, without EXIF metadata."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        icc_profile = original.info.get("icc_profile")
        img = ImageOps.exif_transpose(original)  # EXIF is dropped, so bake in rotation
        img.thumbnail((THUMB_WIDTH, THUMB_MAX_HEIGHT), Image.LANCZOS)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        options = {"icc_profile": icc_profile} if icc_profile else {}
        img.save(dest, "WEBP", quality=THUMB_QUALITY, method=6, **options)


def upload_thumbnail(bucket, local_path: Path, filename: str) -> None:
    """Upload a generated thumbnail to the images bucket."""
    blob = bucket.blob(thumb_path(filename))
    blob.cache_control = THUMB_CACHE_CONTROL
    blob.upload_from_filename(str(local_path), content_type="image/webp")
