"""
Module for interacting with NASA's Mars Rover Photos API.
"""
import logging
import requests
from datetime import datetime
import time
import random
from pathlib import Path

import config

logger = logging.getLogger(__name__)

NASA_API_KEY = config.NASA_API_KEY

# ── Circuit breaker state ────────────────────────────────────────────────────
_consecutive_failures = 0
_backoff_until        = 0.0   # unix timestamp; 0 means "no backoff"
_MAX_BACKOFF_SECONDS  = 60 * 60  # cap at 1 hour

def _record_failure():
    global _consecutive_failures, _backoff_until
    _consecutive_failures += 1
    wait = min(300 * (2 ** (_consecutive_failures - 1)), _MAX_BACKOFF_SECONDS)
    _backoff_until = time.time() + wait
    logger.warning(
        f"Mars API consecutive failures: {_consecutive_failures}. "
        f"Circuit breaker: next retry in {wait // 60} min"
    )

def _record_success():
    global _consecutive_failures, _backoff_until
    _consecutive_failures = 0
    _backoff_until        = 0.0

def _circuit_open() -> bool:
    """Return True when the circuit breaker is blocking requests."""
    if _backoff_until and time.time() < _backoff_until:
        remaining = int(_backoff_until - time.time())
        logger.info(f"Circuit breaker open — skipping Mars API call ({remaining}s remaining)")
        return True
    return False
# ────────────────────────────────────────────────────────────────────────────

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
            response = requests.get(url, params=params, timeout=25)

            if response.status_code == 200:
                data   = response.json()
                photos = data.get('latest_photos', data.get('photos', []))
                if photos:
                    logger.info(f"Successfully fetched {len(photos)} photos from {url}")
                    return photos

            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 3600))
                logger.warning(f"Rate limit (429) from {url}. Backing off {retry_after}s.")
                # Directly set the breaker so the caller backs off
                global _backoff_until
                _backoff_until = time.time() + retry_after
                return []

            else:
                logger.warning(f"Endpoint {url} returned {response.status_code}. "
                               f"Response: {response.text[:150]}")

        except Exception as e:
            logger.error(f"Request to {url} failed: {e}")

    logger.warning("All API attempts failed. Checking local data.")
    return []

def download_photo(photo_data, save_dir=None):
    """
    Download a Mars Rover photo and save it to the specified directory.

    Args:
        photo_data (dict): Photo data from NASA API
        save_dir: Directory to save the photo (defaults to config.NASA_IMAGES_DIR)

    Returns:
        Path: Path to the saved photo, or None if download failed
    """
    if save_dir is None:
        save_dir = config.NASA_IMAGES_DIR
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    img_url = photo_data.get('img_src')
    if not img_url:
        logger.warning("No image URL found in photo data")
        return None

    rover    = photo_data.get('rover', {}).get('name', 'unknown')
    camera   = photo_data.get('camera', {}).get('name', 'unknown')
    photo_id = photo_data.get('id', random.randint(10000, 99999))
    date_str = datetime.now().strftime("%Y%m%d")

    filename = f"{date_str}_{rover}_{camera}_{photo_id}.jpg"
    filepath = save_dir / filename

    if filepath.exists():
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
    Returns the number of new photos saved.
    """
    if _circuit_open():
        return 0

    photos = get_mars_rover_photos()

    if not photos:
        logger.warning("No photos available from latest_photos or specific dates")
        _record_failure()
        return 0

    _record_success()
    
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
