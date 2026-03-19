"""
Module for interacting with NASA's EPIC (Earth Polychromatic Imaging Camera) API.
"""
import os
import logging
import requests
from datetime import datetime, timedelta
import json

# Configure logging
logger = logging.getLogger(__name__)

# Constants
EPIC_API_URL = "https://api.nasa.gov/EPIC/api"
EPIC_IMAGE_URL = "https://epic.gsfc.nasa.gov/archive/natural"

def get_epic_photos(date=None):
    """
    Fetch EPIC photos from NASA API.
    
    Args:
        date (str): Date in the format YYYY-MM-DD, defaults to most recent available
        
    Returns:
        list: List of EPIC photo data objects from NASA API
    """
    # Get NASA API key from environment variable
    api_key = os.environ.get("NASA_API_KEY")
    if not api_key:
        logger.error("NASA_API_KEY environment variable not set")
        return []
    
    # Default to today - 2 days (as EPIC images are usually 2-3 days behind)
    if date is None:
        target_date = datetime.now() - timedelta(days=2)
        date = target_date.strftime('%Y-%m-%d')
    
    try:
        # Try with specific date first
        url = f"{EPIC_API_URL}/natural/date/{date}"
        params = {"api_key": api_key}
        response = requests.get(url, params=params, timeout=30)
        
        # If no images for specific date, try to get available dates and use most recent
        if response.status_code == 404 or (response.status_code == 200 and len(response.json()) == 0):
            logger.info(f"No EPIC images available for {date}, getting most recent date")
            url = f"{EPIC_API_URL}/natural/available"
            dates_response = requests.get(url, params=params, timeout=30)
            
            if dates_response.status_code == 200:
                available_dates = dates_response.json()
                if available_dates:
                    # Use the most recent date
                    most_recent_date = available_dates[-1]
                    logger.info(f"Using most recent EPIC date: {most_recent_date}")
                    url = f"{EPIC_API_URL}/natural/date/{most_recent_date}"
                    response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            photos = response.json()
            logger.info(f"Successfully fetched {len(photos)} EPIC photos")
            return photos
        else:
            logger.error(f"Error fetching EPIC photos: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error in get_epic_photos: {e}")
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
        
        # Get NASA API key from environment variable
        api_key = os.environ.get("NASA_API_KEY", "DEMO_KEY")
        
        # Construct the image URL with API key
        # Format: https://api.nasa.gov/EPIC/archive/natural/2019/05/30/png/epic_1b_20190530003633.png?api_key=DEMO_KEY
        url = f"https://api.nasa.gov/EPIC/archive/natural/{date_path}/png/{image_name}.png?api_key={api_key}"
        
        # Create save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Prepare filename with date and caption for better identification
        caption = photo_data.get('caption', 'earth_view').replace(' ', '_').lower()
        filename = f"epic_{date_obj.strftime('%Y%m%d')}_{caption}_{image_name}.png"
        file_path = os.path.join(save_dir, filename)
        
        # Don't re-download if file already exists
        if os.path.exists(file_path):
            logger.info(f"EPIC photo already exists: {file_path}")
            return file_path
        
        # Download the image
        response = requests.get(url)
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