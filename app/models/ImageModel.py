from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.services.async_database import Base


class Image(Base):
    """
    The Image model represents an image stored in the system.
    """
    __tablename__ = 'images'

    image_id = Column(String, primary_key=True, unique=True)
    file_path = Column(String)
    faces = relationship("Face", back_populates="image")
