import os

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

FACE_API_TOKEN = os.environ.get("FACE_API_TOKEN")
FACE_API_SECRET = os.environ.get("FACE_API_SECRET")
WEATHER_API_TOKEN = os.environ.get("WEATHER_API_TOKEN")