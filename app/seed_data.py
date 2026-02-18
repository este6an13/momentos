from datetime import datetime
from app.database import SessionLocal, init_db
from app.models import Photo

def seed_database():
    """Seed database with sample photo data"""
    init_db()
    db = SessionLocal()
    
    # Check if already seeded
    if db.query(Photo).count() > 0:
        print("Database already seeded")
        db.close()
        return
    
    sample_photos = [
        {
            "filename": "photo_1.jpg",
            "title": "Golden Hour",
            "description": "Sunset over the city skyline",
            "location": "New York, NY",
            "tags": ["sunset", "urban", "cityscape"],
            "taken_at": datetime(2024, 6, 15, 19, 30)
        },
        {
            "filename": "photo_2.jpg",
            "title": "Mountain Vista",
            "description": "Early morning in the mountains",
            "location": "Rocky Mountains, CO",
            "tags": ["landscape", "mountains", "nature"],
            "taken_at": datetime(2024, 7, 22, 6, 15)
        },
        {
            "filename": "photo_3.jpg",
            "title": "Urban Geometry",
            "description": "Abstract architectural patterns",
            "location": "Chicago, IL",
            "tags": ["architecture", "abstract", "urban"],
            "taken_at": datetime(2024, 5, 10, 14, 20)
        },
        {
            "filename": "photo_4.jpg",
            "title": "Ocean Waves",
            "description": "Crashing waves at sunset",
            "location": "Malibu, CA",
            "tags": ["ocean", "sunset", "nature"],
            "taken_at": datetime(2024, 8, 3, 19, 45)
        },
        {
            "filename": "photo_5.jpg",
            "title": "Forest Path",
            "description": "Misty morning trail through the woods",
            "location": "Olympic National Park, WA",
            "tags": ["forest", "nature", "mist"],
            "taken_at": datetime(2024, 9, 12, 7, 0)
        },
        {
            "filename": "photo_6.jpg",
            "title": "Desert Dunes",
            "description": "Sand patterns in the desert",
            "location": "Death Valley, CA",
            "tags": ["desert", "landscape", "abstract"],
            "taken_at": datetime(2024, 4, 18, 16, 30)
        },
        {
            "filename": "photo_7.jpg",
            "title": "Night Lights",
            "description": "City lights from above",
            "location": "Los Angeles, CA",
            "tags": ["night", "urban", "cityscape"],
            "taken_at": datetime(2024, 10, 5, 21, 15)
        },
        {
            "filename": "photo_8.jpg",
            "title": "Autumn Colors",
            "description": "Fall foliage in full display",
            "location": "Vermont",
            "tags": ["autumn", "nature", "landscape"],
            "taken_at": datetime(2024, 10, 20, 11, 30)
        },
        {
            "filename": "photo_9.jpg",
            "title": "Minimalist",
            "description": "Simple lines and shadows",
            "location": None,
            "tags": ["minimal", "abstract", "architecture"],
            "taken_at": datetime(2024, 3, 8, 13, 0)
        },
        {
            "filename": "photo_10.jpg",
            "title": "Coastal Cliffs",
            "description": "Dramatic coastline at dusk",
            "location": "Big Sur, CA",
            "tags": ["coast", "landscape", "sunset"],
            "taken_at": datetime(2024, 11, 2, 18, 20)
        },
        {
            "filename": "photo_11.jpg",
            "title": "Urban Rain",
            "description": "Reflections on wet city streets",
            "location": "Seattle, WA",
            "tags": ["urban", "rain", "reflections"],
            "taken_at": datetime(2024, 11, 15, 17, 45)
        },
        {
            "filename": "photo_12.jpg",
            "title": "Starry Night",
            "description": "Milky Way over the desert",
            "location": "Arizona",
            "tags": ["stars", "night", "landscape"],
            "taken_at": datetime(2024, 8, 25, 23, 30)
        }
    ]
    
    for photo_data in sample_photos:
        photo = Photo(
            filename=photo_data["filename"],
            title=photo_data["title"],
            description=photo_data["description"],
            location=photo_data["location"],
            taken_at=photo_data["taken_at"]
        )
        photo.set_tags(photo_data["tags"])
        db.add(photo)
    
    db.commit()
    db.close()
    print(f"Seeded database with {len(sample_photos)} photos")

if __name__ == "__main__":
    seed_database()
