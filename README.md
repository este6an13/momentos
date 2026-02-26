# Photo Gallery

A lightweight, dark-mode photo gallery built with FastAPI, HTMX, and SQLite.

## Features

- 🌙 Beautiful dark mode aesthetic
- ⚡ Fast and lightweight with HTMX
- 📱 Responsive design
- 🏷️ Photo metadata (title, description, location, tags)
- 🗄️ SQLite database for easy setup

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate placeholder images:**
   ```bash
   python generate_images.py
   ```

3. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Open your browser:**
   Navigate to `http://localhost:8000`

## Project Structure

```
photo-gallery/
├── app/
│   ├── main.py          # FastAPI application
│   ├── models.py        # Database models
│   ├── database.py      # Database configuration
│   └── seed_data.py     # Sample data
├── static/
│   ├── css/
│   │   └── style.css    # Dark mode styling
│   └── images/          # Photo files
├── templates/
│   ├── base.html        # Base template
│   ├── index.html       # Main gallery page
│   ├── photo_grid.html  # Photo grid partial
│   └── photo_detail.html # Photo detail modal
├── photos.db            # SQLite database (created on first run)
└── requirements.txt     # Python dependencies
```

## Technology Stack

- **Backend:** FastAPI (Python)
- **Frontend:** HTMX + Vanilla CSS
- **Database:** SQLite
- **Styling:** Dark mode with modern CSS

## Roadmap

- UI Enhancements
- Trigger DB Download w/o Deployment
- Domain
