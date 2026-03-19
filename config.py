"""
Central configuration: all paths, environment variables and constants in one place.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

NASA_IMAGES_DIR = DATA_DIR / "nasa_images"
NASA_APOD_DIR   = DATA_DIR / "nasa_apod"
NASA_EPIC_DIR   = DATA_DIR / "nasa_epic"

ANIMATION_MP4 = DATA_DIR / "nasa_animation.mp4"
ANIMATION_GIF = DATA_DIR / "nasa_animation.gif"

NASA_API_KEY       = os.getenv("NASA_API_KEY", "DEMO_KEY")
SESSION_SECRET     = os.getenv("SESSION_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))

FETCH_INTERVAL_SECONDS = 2.4 * 60
APOD_UPDATE_TIME       = "00:30"
EPIC_UPDATE_TIME       = "01:00"
ANIMATION_CREATE_TIME  = "16:00"
ANIMATION_SEND_TIME    = "16:05"
