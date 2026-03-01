# Momentos

A lightweight, dark-mode photo gallery built with FastAPI, HTMX, Vanilla CSS, and SQLite, meant to be a quiet, personal space to share moments captured in time.

## Philosophy

This gallery is a personal project; a place to share photos without algorithmic timelines, ads, or pressure to perform. Things that aren’t possible on platforms like Instagram or VSCO.

- **Intentionally Quiet**: There’s no algorithm deciding what should be seen, no pressure to post regularly, and no need to compete for attention. Just a personal collection open to anyone who chooses to look.
- **Mutable**: I wanted a feed that I could adjust over time: editing details, changing descriptions, and reordering images.
- **Explorable**: Visitors can view photos chronologically or shuffle them at random, and search the archive using keywords, making it easier to explore the collection at their own pace.

## Features

- **Dark Mode Aesthetic**: Influenced by minimalist and modern photo editing applications.
- **Lightweight**: Uses HTMX to avoid full-page reloads and enable features like endless scrolling, photo modals, and live-search.
- **Responsive & Intuitive Design**: Enjoyable on desktop and mobile, with swipe gesture support for iterating through photos and auto-hiding navigation.
- **Photo Metadata & Search**: Granular metadata (title, description, location, tags, date), with a fast search system.
- **Self-Hostable**: Runs locally with SQLite + local images layer, or can be deployed to Google Cloud Run with images and DB served from a Google Cloud Storage bucket.
- **Local Admin UI**: Access to an admin interface to upload and edit photos locally.

## Technology Stack

- **Backend:** FastAPI (Python)
- **Frontend:** HTMX + Vanilla CSS
- **Database:** SQLite

## Running Locally

1. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

2. **Set up `.env` (optional for local, required for GCP integration/Admin Mode):**
   ```bash
   cp .env.example .env
   # Edit .env with your ADMIN_MODE=true and WEBHOOK_TOKEN flags to test the uploader UI locally
   ```

3. **Run the application:**
   ```bash
   uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

4. **View the Gallery:**
   Navigate to `http://localhost:8000`

## Deployment Strategy

The project can be deployed to **Google Cloud Run**, with images served from a **Google Cloud Storage (GCS)** bucket.

1. **Environment Setup**: Set `STORAGE_BACKEND=gcp`, `GCP_BUCKET_NAME={bucket}` in a Cloud Run container environment.
2. **Uploading**: Use `ADMIN_MODE=true` to access the protected `/upload` interface, which uploads the photos directly into the GCS bucket while storing the metadata in a SQLite DB.
3. **Database Syncing**: Because Cloud Run is stateless, the `photos.db` SQLite file is synced to the private storage bucket. 
    - The `sync_db_to_gcp.py` script pushes the latest local database to the cloud. You can run it with:
      ```bash
      uv run py scripts/sync_db_to_gcp.py
      ```
    - Cloud Run grabs exactly this `.db` file on startup or receives automated webhook pings to download updates.

4. **Deploying to Cloud Run**: You can deploy the application using the deployment script:
   ```bash
   uv run py scripts/deploy.py
   ```
