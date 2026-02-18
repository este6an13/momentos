from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import json

Base = declarative_base()


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False, unique=True, index=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    taken_at = Column(DateTime, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    tags = Column(Text, nullable=True)  # JSON string
    exif_data = Column(Text, nullable=True)  # JSON string, reserved for future EXIF

    def get_tags(self):
        """Parse tags from JSON string"""
        if self.tags:
            try:
                return json.loads(self.tags)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def set_tags(self, tag_list):
        """Set tags as JSON string"""
        self.tags = json.dumps(tag_list)
