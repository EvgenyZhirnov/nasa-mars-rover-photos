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

def get_apod():
    from nasa_hub import apod
    try:
        return apod()
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.warning("APOD metadata unavailable: %s", type(exc).__name__)
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
    
    img_url = apod_data.get('image_url') or apod_data.get('hdurl')
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
        if not response.headers.get('Content-Type', '').lower().startswith('image/'):
            logger.warning('APOD download was not an image')
            return None, apod_data
        
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