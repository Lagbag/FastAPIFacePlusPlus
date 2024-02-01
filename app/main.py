from fastapi import FastAPI

from app.routers import user
from app.services.async_database import init_db

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World"}

app.include_router(user.router)


@app.on_event("startup")
async def startup_event():
    await init_db()