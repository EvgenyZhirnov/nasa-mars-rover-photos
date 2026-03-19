"""
Module for interacting with NASA's Mars Rover Photos API.
"""
import os
import logging
import requests
from datetime import datetime, timedelta
import time
import random
import utils

logger = logging.getLogger(__name__)

# NASA API base URL and endpoint
NASA_API_BASE_URL = "https://api.nasa.gov/mars-photos/api/v1"
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

def get_mars_rover_photos(rover="curiosity", date=None):
    """
    Fetch Mars Rover photos from NASA API.
    """
    api_key = NASA_API_KEY
    
    # NASA API documentation: 
    # https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos?sol=1000&api_key=DEMO_KEY
    
    attempts = [
        # Attempt 1: Standard NASA API Sol 1000 (Very stable)
        ("https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos", {"sol": "1000", "api_key": api_key}),
        # Attempt 2: Perseverance latest_photos
        ("https://api.nasa.gov/mars-photos/api/v1/rovers/perseverance/latest_photos", {"api_key": api_key}),
        # Attempt 3: Heroku mirror
        ("https://mars-photos.herokuapp.com/api/v1/rovers/curiosity/latest_photos", {}),
    ]

    for url, params in attempts:
        try:
            logger.info(f"Attempting NASA API: {url}")
            # Ensure the params are passed as a dict, and requests handles the encoding
            response = requests.get(url, params=params, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                photos = data.get('latest_photos', data.get('photos', []))
                if photos:
                    logger.info(f"Successfully fetched {len(photos)} photos from {url}")
                    return photos
            
            logger.warning(f"Endpoint {url} returned {response.status_code}. Response: {response.text[:200]}")
        except Exception as e:
            logger.error(f"Request to {url} failed: {e}")
            
    # Fallback: if even NASA is down, we check if we have ANY images locally to show
    logger.warning("All API attempts failed. Checking local data.")
    return []

def download_photo(photo_data, save_dir="data/nasa_images"):
    """
    Download a Mars Rover photo and save it to the specified directory.
    
    Args:
        photo_data (dict): Photo data from NASA API
        save_dir (str): Directory to save the photo
        
    Returns:
        str: Path to the saved photo, or None if download failed
    """
    img_url = photo_data.get('img_src')
    if not img_url:
        logger.warning("No image URL found in photo data")
        return None
    
    # Generate a unique filename
    rover = photo_data.get('rover', {}).get('name', 'unknown')
    camera = photo_data.get('camera', {}).get('name', 'unknown')
    photo_id = photo_data.get('id', random.randint(10000, 99999))
    date_str = datetime.now().strftime("%Y%m%d")
    
    filename = f"{date_str}_{rover}_{camera}_{photo_id}.jpg"
    filepath = os.path.join(save_dir, filename)
    
    # Check if file already exists
    if os.path.exists(filepath):
        logger.info(f"Photo already exists: {filepath}")
        return filepath
    
    try:
        logger.info(f"Downloading photo from {img_url}")
        response = requests.get(img_url, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
            
        logger.info(f"Successfully saved photo to {filepath}")
        return filepath
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading photo from {img_url}: {e}")
        return None
    except IOError as e:
        logger.error(f"Error saving photo to {filepath}: {e}")
        return None

def fetch_and_save_photos():
    """
    Fetch new Mars Rover photos and save them to the data directory.
    
    Returns:
        int: Number of new photos saved
    """
    # Try getting latest photos directly
    photos = get_mars_rover_photos()
    
    if not photos:
        logger.warning("No photos available from latest_photos or specific dates")
        return 0
    
    # Randomly select a sample of photos (max 5) to avoid too many downloads
    sample_size = min(5, len(photos))
    selected_photos = random.sample(photos, sample_size)
    
    saved_count = 0
    for photo in selected_photos:
        filepath = download_photo(photo)
        if filepath:
            saved_count += 1
            # Add a small delay to avoid overwhelming the server
            time.sleep(0.5)
    
    logger.info(f"Saved {saved_count} new photos")
    return saved_count
