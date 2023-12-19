import io
import os
from typing import List, Optional

import aiofiles
import aiohttp
from PIL import Image as PILImage, ImageDraw
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.params import Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.FaceModel import Face
from app.models.ImageModel import Image
from app.schema.ImageSchema import GetImageParams, CompareFacesResponse, CompareFacesRequest, ImageDeletionResponse
from app.services.config import FACE_API_TOKEN, FACE_API_SECRET
from app.services.async_database import get_async_session

router = APIRouter(
    prefix="/face",
    tags=["face"],
    dependencies=[],
    responses={404: {"description": "Not found"}},

)


@router.post("/upload_image")
async def upload_image(file: UploadFile = File(...), session: AsyncSession = Depends(get_async_session)) -> JSONResponse:
    """
        Upload an image and analyze it for faces using the FacePlusPlus API.

        Args:
            file (UploadFile): The image file to be uploaded and analyzed.
            session (AsyncSession): Dependency injection of the SQLAlchemy async session for database operations.

        Returns:
            JSONResponse: A response JSON containing the image ID and tokens of detected faces.

        Raises:
            HTTPException: If the image format is invalid or if the FacePlusPlus API request fails.
        """
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    file_content = await file.read()

    data = aiohttp.FormData()
    data.add_field('api_key', FACE_API_TOKEN)
    data.add_field('api_secret', FACE_API_SECRET)
    data.add_field('image_file', file_content, filename=file.filename, content_type='multipart/form-data')

    async with aiohttp.ClientSession() as http_session:
        async with http_session.post("https://api-us.faceplusplus.com/facepp/v3/detect", data=data) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="Error from FacePlusPlus API")
            face_data = await response.json()

    existing_image = await session.execute(select(Image).filter_by(image_id=face_data['image_id']))
    existing_image = existing_image.scalars().first()
    if existing_image:
        raise HTTPException(status_code=400, detail=f"Image already exists with ID: {face_data['image_id']}")

    file_path = os.path.join(os.getcwd(), 'app', 'images', file.filename)
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(file_content)

    new_image = Image(image_id=face_data['image_id'], file_path=file_path)
    face_objects = []
    for face in face_data['faces']:
        new_face = Face(face_token=face['face_token'], face_rectangle=face['face_rectangle'], image=new_image)
        session.add(new_face)
        face_objects.append(new_face)

    session.add(new_image)
    await session.commit()

    return JSONResponse(content={"image_id": face_data['image_id'],
                                 "faces_token": [face['face_token'] for face in face_data['faces']]})


@router.get("/image/{image_id}")
async def get_image(params: GetImageParams = Depends(), faces: List[str] = Query(None), session: AsyncSession = Depends(get_async_session)):
    """
        Retrieve and modify an image by highlighting specified faces.

        Args:
            params (GetImageParams): color for highlighting, image_id it's unique identifier of the image and face tokens.
            session (AsyncSession): Dependency injection for the database session.

        Returns:
            Response: A modified image with highlighted faces, if specified.

        Raises:
            HTTPException: If the image is not found or an error occurs during image processing.
        """
    result = await session.execute(select(Image).filter_by(image_id=params.image_id))
    image_record = result.scalars().first()
    if not image_record:
        raise HTTPException(status_code=404, detail="Image not found")

    face_records = await session.execute(select(Face).where(Face.image_id == params.image_id))
    face_records = face_records.scalars().all()

    try:
        with open(image_record.file_path, "rb") as file:
            image = PILImage.open(file)

            draw = ImageDraw.Draw(image)
            for face in face_records:
                if faces is not None:
                    if face.face_token in faces:
                        rect = (face.face_rectangle['left'], face.face_rectangle['top'],
                                face.face_rectangle['left'] + face.face_rectangle['width'],
                                face.face_rectangle['top'] + face.face_rectangle['height'])
                        try:
                            draw.rectangle(rect, outline=params.color)
                        except ValueError:
                            raise HTTPException(status_code=400, detail=f"Unknown color specifier '{params.color}'")

            img_format = 'JPEG'
            if image_record.file_path.lower().endswith('.png'):
                img_format = 'PNG'

            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=img_format)
            img_byte_arr = img_byte_arr.getvalue()

            return Response(content=img_byte_arr, media_type=f"image/{img_format.lower()}")
    except IOError:
        raise HTTPException(status_code=500, detail="Error reading image file")


@router.get("/compare-faces", response_model=CompareFacesResponse)
async def face_compare(params: CompareFacesRequest = Depends(CompareFacesRequest),
                       session: AsyncSession = Depends(get_async_session)) -> CompareFacesResponse:
    """
        Compare two faces based on their tokens using the FacePlusPlus API.

        Args:
            params (CompareFacesRequest): The request model containing the tokens of the two faces to compare.
            session (AsyncSession): Dependency injection for the database session.

        Returns:
            CompareFacesResponse: The response model containing the confidence score of the face comparison.

        Raises:
            HTTPException: If one or both faces are not found in the database, or if there is an error from the FacePlusPlus API.
        """
    face1 = await session.execute(select(Face).where(Face.face_token == params.face_token1))
    face2 = await session.execute(select(Face).where(Face.face_token == params.face_token2))

    face1 = face1.scalars().first()
    face2 = face2.scalars().first()

    if not face1 or not face2:
        raise HTTPException(status_code=404, detail="One or both faces not found in database")

    data = aiohttp.FormData()
    data.add_field('api_key', FACE_API_TOKEN)
    data.add_field('api_secret', FACE_API_SECRET)
    data.add_field('face_token1', params.face_token1)
    data.add_field('face_token2', params.face_token2)

    async with aiohttp.ClientSession() as http_session:
        async with http_session.post(f"https://api-us.faceplusplus.com/facepp/v3/compare", data=data) as response:
            if response.status != 200:
                raise HTTPException(status_code=404, detail="Error from FacePlusPlus API")
            data = await response.json()
            return CompareFacesResponse(confidence=data['confidence'])


@router.delete("/image/{image_id}", response_model=ImageDeletionResponse)
async def delete_image(image_id: str, session: AsyncSession = Depends(get_async_session)) -> ImageDeletionResponse:
    """
        Deletes an image and its associated face records from the database.

        Args:
            image_id (str): The unique identifier of the image to be deleted.
            session (AsyncSession): Dependency injection for the database session.

        Returns:
            ImageDeletionResponse: A response model indicating the success of the operation.

        Raises:
            HTTPException: If the image with the specified ID is not found in the database.
        """

    result = await session.execute(select(Image).filter_by(image_id=image_id))
    image_record = result.scalars().first()

    if not image_record:
        raise HTTPException(status_code=404, detail="Image not found")

    await session.execute(delete(Face).where(Face.image_id == image_id))
    await session.delete(image_record)
    await session.commit()

    return ImageDeletionResponse(status="success", message="Image and associated faces deleted")
