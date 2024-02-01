from fastapi import FastAPI

from app.routers import face_recognize
from app.services.async_database import init_db
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}

# app.include_router(face_recognize.router)


@app.on_event("startup")
async def startup_event():
    await init_db()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")