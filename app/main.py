from fastapi import FastAPI

from app.routers import face_recognize
from app.services.async_database import init_db

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}

app.include_router(face_recognize.router)


@app.on_event("startup")
async def startup_event():
    await init_db()
