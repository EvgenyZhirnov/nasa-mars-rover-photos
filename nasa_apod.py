"""
Module for interacting with NASA's Astronomy Picture of the Day (APOD) API.
"""
import os
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

def download_apod(save_dir="data/nasa_apod"):
    """
    Download the Astronomy Picture of the Day and save it to the specified directory.
    
    Args:
        save_dir (str): Directory to save the photo
        
    Returns:
        tuple: (path to the saved photo, apod data) or (None, None) if download failed
    """
    apod_data = get_apod()
    
    if not apod_data:
        logger.warning("Could not fetch APOD data")
        return None, None
    
    # Check if the APOD is a video
    if apod_data.get('media_type') != 'image':
        logger.info(f"APOD is not an image (media_type: {apod_data.get('media_type')})")
        return None, apod_data
    
    img_url = apod_data.get('url')
    if not img_url:
        logger.warning("No image URL found in APOD data")
        return None, apod_data
    
    # Ensure directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate a filename
    date_str = apod_data.get('date', datetime.now().strftime("%Y-%m-%d"))
    title = apod_data.get('title', 'apod').replace(' ', '_').lower()
    
    # Determine file extension from URL
    extension = os.path.splitext(img_url)[1]
    if not extension:
        extension = '.jpg'  # Default to jpg if no extension found
    
    filename = f"apod_{date_str}_{title}{extension}"
    filepath = os.path.join(save_dir, filename)
    
    # Check if file already exists
    if os.path.exists(filepath):
        logger.info(f"APOD already exists: {filepath}")
        return filepath, apod_data
    
    try:
        logger.info(f"Downloading APOD from {img_url}")
        response = requests.get(img_url, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
            
        logger.info(f"Successfully saved APOD to {filepath}")
        return filepath, apod_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading APOD from {img_url}: {e}")
        return None, apod_data
    except IOError as e:
        logger.error(f"Error saving APOD to {filepath}: {e}")
        return None, apod_data