"""
Module for creating animations from Mars Rover photos.
"""
import os
import logging
import glob
from datetime import datetime
import imageio
import re

logger = logging.getLogger(__name__)

def create_animation(source_dir="data/nasa_images", output_file="data/nasa_animation.mp4", fps=2):
    """
    Create an animation from all images saved on the current day.
    
    Args:
        source_dir (str): Directory containing the source images
        output_file (str): Path to save the output animation
        fps (int): Frames per second for the animation
        
    Returns:
        str: Path to the created animation file, or None if creation failed
    """
    try:
        # Get today's date in YYYYMMDD format
        today = datetime.now().strftime("%Y%m%d")
        
        # Find all images from today
        pattern = os.path.join(source_dir, f"{today}_*.jpg")
        image_files = sorted(glob.glob(pattern))
        
        if not image_files:
            logger.warning(f"No images found for today ({today}) in {source_dir}")
            
            # As a fallback, try to get the most recent day's images
            all_images = glob.glob(os.path.join(source_dir, "*.jpg"))
            if not all_images:
                logger.error("No images found at all")
                return None
                
            # Extract dates from filenames and find the most recent
            dates = set()
            for img in all_images:
                match = re.search(r"(\d{8})_", os.path.basename(img))
                if match:
                    dates.add(match.group(1))
            
            if not dates:
                logger.error("Could not extract dates from filenames")
                return None
                
            most_recent = sorted(dates, reverse=True)[0]
            logger.info(f"Using images from {most_recent} instead")
            
            pattern = os.path.join(source_dir, f"{most_recent}_*.jpg")
            image_files = sorted(glob.glob(pattern))
            
            if not image_files:
                logger.error(f"No images found for {most_recent} either")
                return None
        
        logger.info(f"Creating animation from {len(image_files)} images")
        
        # Create animation
        output_dir = os.path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)
        
        # Read images
        images = []
        for img_path in image_files:
            try:
                img = imageio.imread(img_path)
                images.append(img)
            except Exception as e:
                logger.error(f"Error reading image {img_path}: {e}")
        
        if not images:
            logger.error("No valid images could be read")
            return None
            
        # Create MP4 animation
        try:
            writer = imageio.get_writer(output_file, fps=fps)
            for img in images:
                writer.append_data(img)
            writer.close()
            logger.info(f"Successfully created animation at {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error creating MP4 animation: {e}")
            
            # Try creating GIF as a fallback
            try:
                gif_output = output_file.replace('.mp4', '.gif')
                imageio.mimsave(gif_output, images, fps=fps)
                logger.info(f"Successfully created GIF animation at {gif_output}")
                return gif_output
            except Exception as e2:
                logger.error(f"Error creating GIF animation: {e2}")
                return None
                
    except Exception as e:
        logger.error(f"Unexpected error in create_animation: {e}")
        return None
