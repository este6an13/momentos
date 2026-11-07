"""
Create thumbnails for photos that don't have one yet.

Safe to re-run: existing thumbnails are skipped and originals are never changed.

    uv run py scripts/generate_thumbnails.py --dry-run
    uv run py scripts/generate_thumbnails.py --limit 3
    uv run py scripts/generate_thumbnails.py
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

# Add the parent directory to the Python path so we can import app modules
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.thumbnails import THUMB_DIR, make_thumbnail, thumb_path, upload_thumbnail

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def is_image(name: str) -> bool:
    return Path(name).suffix.lower() in IMAGE_EXTENSIONS


def run_gcp(limit, dry_run):
    from google.cloud import storage

    bucket_name = os.environ.get("GCP_BUCKET_NAME")
    if not bucket_name:
        sys.exit("Error: GCP_BUCKET_NAME not set in .env")

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    names = [b.name for b in client.list_blobs(bucket_name)]
    existing = {n for n in names if n.startswith(f"{THUMB_DIR}/")}
    missing = [n for n in names if "/" not in n and is_image(n) and thumb_path(n) not in existing]

    print(f"{len(missing)} photos need a thumbnail ({len(existing)} already exist)")
    todo = missing[:limit] if limit else missing
    if dry_run:
        return 0

    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for i, name in enumerate(todo, 1):
            source = Path(tmp) / name
            dest = Path(tmp) / f"{name}.webp"
            try:
                bucket.blob(name).download_to_filename(str(source))
                make_thumbnail(source, dest)
                upload_thumbnail(bucket, dest, name)
                print(f"[{i}/{len(todo)}] {name}: {source.stat().st_size // 1000} KB -> {dest.stat().st_size // 1000} KB")
            except Exception as e:
                failed += 1
                print(f"[{i}/{len(todo)}] {name}: FAILED ({e})")
            finally:
                source.unlink(missing_ok=True)
                dest.unlink(missing_ok=True)
    return failed


def run_local(limit, dry_run):
    images_dir = ROOT / "static" / "images"
    names = [f.name for f in images_dir.iterdir() if f.is_file() and is_image(f.name)]
    missing = [n for n in names if not (images_dir / thumb_path(n)).exists()]

    print(f"{len(missing)} photos need a thumbnail")
    todo = missing[:limit] if limit else missing
    if dry_run:
        return 0

    failed = 0
    for i, name in enumerate(todo, 1):
        try:
            make_thumbnail(images_dir / name, images_dir / thumb_path(name))
            print(f"[{i}/{len(todo)}] {name}")
        except Exception as e:
            failed += 1
            print(f"[{i}/{len(todo)}] {name}: FAILED ({e})")
    return failed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, help="only process this many photos")
    parser.add_argument("--dry-run", action="store_true", help="report what's missing without changing anything")
    args = parser.parse_args()

    backend = os.environ.get("STORAGE_BACKEND", "local").lower()
    failed = (run_gcp if backend == "gcp" else run_local)(args.limit, args.dry_run)
    if failed:
        sys.exit(f"{failed} photos failed; re-run to retry them.")


if __name__ == "__main__":
    main()
