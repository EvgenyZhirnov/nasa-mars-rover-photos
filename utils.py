"""
Utility functions for the NASA Mars Rover Photos application.
"""
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_yesterday_date():
    """
    Get yesterday's date in YYYY-MM-DD format.
    
    Returns:
        str: Yesterday's date in YYYY-MM-DD format
    """
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

def get_animation_path():
    """
    Get the path to the latest animation file.
    
    Returns:
        str: Path to the animation file or None if not found
    """
    mp4_path = "/data/nasa_animation.mp4"
    gif_path = "/data/nasa_animation.gif"
    
    if os.path.exists(mp4_path):
        return mp4_path
    elif os.path.exists(gif_path):
        return gif_path
    else:
        return None

def get_image_count():
    """
    Get the count of images in the NASA images directory.
    
    Returns:
        int: Number of images in the directory
    """
    image_dir = "/data/nasa_images"
    
    if not os.path.exists(image_dir):
        return 0
        
    try:
        files = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
        return len(files)
    except Exception as e:
        logger.error(f"Error counting files in {image_dir}: {e}")
        return 0

def get_today_images():
    """
    Get the count of images from today in the NASA images directory.
    
    Returns:
        int: Number of images from today
    """
    image_dir = "/data/nasa_images"
    today = datetime.now().strftime("%Y%m%d")
    
    if not os.path.exists(image_dir):
        return 0
        
    try:
        files = [f for f in os.listdir(image_dir) if f.startswith(today) and f.endswith(('.jpg', '.jpeg', '.png'))]
        return len(files)
    except Exception as e:
        logger.error(f"Error counting today's files in {image_dir}: {e}")
        return 0
