"""
Module for interacting with NASA's EPIC (Earth Polychromatic Imaging Camera) API.
"""
import os
import logging
import requests
from datetime import datetime
import json

# Configure logging
logger = logging.getLogger(__name__)

# Constants
EPIC_API_URL = "https://api.nasa.gov/EPIC/api"
EPIC_IMAGE_URL = "https://epic.gsfc.nasa.gov/archive/natural"

def get_epic_photos(date=None):
    from nasa_hub import get_json
    suffix = f"/date/{date}" if date else ""
    try:
        return get_json(f"https://epic.gsfc.nasa.gov/api/natural{suffix}")
    except (requests.RequestException, ValueError):
        logger.warning("EPIC metadata unavailable")
        return []

def download_epic_photo(photo_data, save_dir="data/nasa_epic"):
    """
    Download an EPIC photo and save it to the specified directory.
    
    Args:
        photo_data (dict): Photo data from NASA EPIC API
        save_dir (str): Directory to save the photo
        
    Returns:
        str: Path to the saved photo, or None if download failed
    """
    try:
        # Extract date and image name from photo data
        image_name = photo_data.get('image')
        date_str = photo_data.get('date')
        
        if not image_name or not date_str:
            logger.error("Missing image name or date in EPIC photo data")
            return None
        
        # Parse date for URL construction (YYYY/MM/DD)
        date_obj = datetime.strptime(date_str.split(' ')[0], '%Y-%m-%d')
        date_path = date_obj.strftime('%Y/%m/%d')
        
        # Direct NASA EPIC archive; use half-resolution JPEGs for local storage.
        url = f"https://epic.gsfc.nasa.gov/archive/natural/{date_path}/jpg/{image_name}.jpg"
        
        # Create save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Prepare filename with date and caption for better identification
        caption = photo_data.get('caption', 'earth_view').replace(' ', '_').lower()
        filename = f"epic_{date_obj.strftime('%Y%m%d')}_{caption}_{image_name}.jpg"
        file_path = os.path.join(save_dir, filename)
        
        # Don't re-download if file already exists
        if os.path.exists(file_path):
            logger.info(f"EPIC photo already exists: {file_path}")
            return file_path
        
        # Download the image
        response = requests.get(url, timeout=(5, 30))
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Downloaded EPIC photo: {file_path}")
            return file_path
        else:
            logger.error(f"Error downloading EPIC photo: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error in download_epic_photo: {e}")
        return None

def save_centroid_metadata(photos, save_dir):
    """
    Persist the centroid_coordinates of the first EPIC photo in the batch so
    the web server can look up the visible hemisphere without making API calls.
    """
    if not photos:
        return
    first = photos[0]
    centroid = first.get("centroid_coordinates", {})
    date_str = first.get("date", "")
    meta = {
        "lat":  centroid.get("lat", 0),
        "lon":  centroid.get("lon", 0),
        "date": date_str,
    }
    meta_path = os.path.join(save_dir, "centroid.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f)
    logger.info(f"Saved EPIC centroid metadata: lat={meta['lat']}, lon={meta['lon']}")


def download_all_epic_photos(date=None, save_dir="data/nasa_epic"):
    """
    Download all EPIC photos for a specific date and save them to the specified directory.
    
    Args:
        date (str): Date in the format YYYY-MM-DD, defaults to most recent available
        save_dir (str): Directory to save the photos
        
    Returns:
        tuple: (number of photos downloaded, list of saved file paths)
    """
    # Create save directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    # Get EPIC photos data
    photos = get_epic_photos(date)
    
    if not photos:
        logger.warning("No EPIC photos available to download")
        return 0, []
    
    # Save centroid metadata for geolocation feature
    save_centroid_metadata(photos, save_dir)
    
    # Download each photo
    downloaded_count = 0
    saved_paths = []
    
    for photo in photos:
        file_path = download_epic_photo(photo, save_dir)
        if file_path:
            downloaded_count += 1
            saved_paths.append(file_path)
    
    logger.info(f"Downloaded {downloaded_count} EPIC photos")
    return downloaded_count, saved_paths

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test downloading EPIC photos
    count, paths = download_all_epic_photos()
    print(f"Downloaded {count} EPIC photos:")
    for path in paths:
        print(f"  - {path}")
