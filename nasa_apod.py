"""
Module for interacting with NASA's Astronomy Picture of the Day (APOD) API.
"""
import os
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
import config
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# NASA API base URL and endpoint
NASA_API_BASE_URL = "https://api.nasa.gov/planetary/apod"
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")  # Use demo key if not provided

def get_apod():
    """
    Fetch the Astronomy Picture of the Day from NASA API.
    
    Returns:
        dict: APOD data from NASA API
    """
    url = NASA_API_BASE_URL
    params = {
        "api_key": NASA_API_KEY
    }
    
    logger.info("Fetching NASA Astronomy Picture of the Day")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Successfully fetched APOD: {data.get('title')}")
        return data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching APOD: {e}")
        return None

def get_cached_apod(save_dir=None):
    directory = Path(save_dir) if save_dir is not None else config.NASA_APOD_DIR
    try:
        data = json.loads((directory / "metadata.json").read_text())
        if not isinstance(data, dict):
            return None
        if data.get("media_type") == "image":
            filename = data.get("local_filename", "")
            if not filename or Path(filename).name != filename or not (directory / filename).is_file():
                return None
            data["file_path"] = f"/apod/image/{filename}"
        return data
    except (OSError, ValueError, TypeError):
        return None


def _cache_apod(data, directory, filename=None):
    payload = dict(data)
    payload["local_filename"] = filename
    temporary = directory / "metadata.json.tmp"
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    temporary.replace(directory / "metadata.json")


def download_apod(save_dir=None):
    """
    Download the Astronomy Picture of the Day and save it to the specified directory.
    
    Args:
        save_dir (str): Directory to save the photo
        
    Returns:
        tuple: (path to the saved photo, apod data) or (None, None) if download failed
    """
    save_dir = Path(save_dir) if save_dir is not None else config.NASA_APOD_DIR
    save_dir.mkdir(parents=True, exist_ok=True)
    apod_data = get_apod()
    
    if not apod_data:
        logger.warning("Could not fetch APOD data")
        return None, None
    
    # Check if the APOD is a video
    if apod_data.get('media_type') != 'image':
        logger.info(f"APOD is not an image (media_type: {apod_data.get('media_type')})")
        _cache_apod(apod_data, save_dir)
        return None, apod_data
    
    img_url = apod_data.get('url')
    if not img_url:
        logger.warning("No image URL found in APOD data")
        return None, apod_data
    
    # Ensure directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate a filename
    date_str = re.sub(r'[^0-9-]', '', apod_data.get('date', datetime.now().strftime("%Y-%m-%d")))
    title = re.sub(r'[^a-z0-9_-]', '_', apod_data.get('title', 'apod').lower())[:100]
    
    # Determine file extension from URL
    extension = Path(urlsplit(img_url).path).suffix.lower()
    if extension not in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
        extension = '.jpg'  # Default to jpg if no extension found
    
    filename = f"apod_{date_str}_{title}{extension}"
    filepath = os.path.join(save_dir, filename)
    
    # Check if file already exists
    if os.path.exists(filepath):
        logger.info(f"APOD already exists: {filepath}")
        _cache_apod(apod_data, save_dir, filename)
        return filepath, apod_data
    
    try:
        logger.info(f"Downloading APOD from {img_url}")
        response = requests.get(img_url, timeout=30)
        response.raise_for_status()
        
        temporary = Path(filepath + '.tmp')
        temporary.write_bytes(response.content)
        temporary.replace(filepath)
            
        logger.info(f"Successfully saved APOD to {filepath}")
        _cache_apod(apod_data, save_dir, filename)
        return filepath, apod_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading APOD from {img_url}: {e}")
        return None, apod_data
    except IOError as e:
        logger.error(f"Error saving APOD to {filepath}: {e}")
        return None, apod_data