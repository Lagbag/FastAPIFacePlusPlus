from sqlalchemy import Column, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import relationship
from app.services.async_database import Base


class Face(Base):
    """
    The Face model represents the data about a face detected in an image.
    """

    __tablename__ = 'faces'

    id = Column(Integer, primary_key=True)
    face_token = Column(String, nullable=False)
    face_rectangle = Column(JSON, nullable=False)
    image_id = Column(String, ForeignKey('images.image_id'), nullable=False)
    image = relationship("Image", back_populates="faces")
