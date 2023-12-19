from fastapi.params import Query
from pydantic import BaseModel, Field
from typing import List, Optional


class GetImageParams(BaseModel):
    image_id: str = Field(description="the ID that is issued after the image is uploaded")
    color: Optional[str] = Field(default="red", description="Color of the rectangle to highlight faces.")


class CompareFacesRequest(BaseModel):
    face_token1: str = Field(description="First face token")
    face_token2: str = Field(description="Second face token")


class CompareFacesResponse(BaseModel):
    confidence: float = Field(description="Confidence")


class ImageDeletionResponse(BaseModel):
    status: str
    message: str
