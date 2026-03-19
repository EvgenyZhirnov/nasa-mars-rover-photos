"""
Creates MP4 (or GIF fallback) animations from saved Mars Rover photos.
"""
import logging
import glob
import re
from datetime import datetime
from pathlib import Path
import imageio

import config

logger = logging.getLogger(__name__)


def create_animation(
    source_dir: Path = config.NASA_IMAGES_DIR,
    output_file: Path = config.ANIMATION_MP4,
    fps: int = 2,
):
    """
    Build an animation from today's (or most recent) rover images.

    Returns the path of the created file, or None on failure.
    """
    source_dir  = Path(source_dir)
    output_file = Path(output_file)

    today   = datetime.now().strftime("%Y%m%d")
    pattern = str(source_dir / f"{today}_*.jpg")
    image_files = sorted(glob.glob(pattern))

    if not image_files:
        logger.warning(f"No images for today ({today}); looking for most recent batch")
        all_images = glob.glob(str(source_dir / "*.jpg"))
        if not all_images:
            logger.error("No rover images available at all")
            return None

        dates = set()
        for img in all_images:
            m = re.search(r"(\d{8})_", Path(img).name)
            if m:
                dates.add(m.group(1))

        if not dates:
            logger.error("Could not extract dates from filenames")
            return None

        most_recent = sorted(dates, reverse=True)[0]
        image_files = sorted(glob.glob(str(source_dir / f"{most_recent}_*.jpg")))
        logger.info(f"Using {len(image_files)} images from {most_recent}")

    if not image_files:
        logger.error("Still no images found after fallback")
        return None

    output_file.parent.mkdir(parents=True, exist_ok=True)

    images = []
    for path in image_files:
        try:
            images.append(imageio.imread(path))
        except Exception as e:
            logger.error(f"Skipping unreadable image {path}: {e}")

    if not images:
        logger.error("No valid images could be read")
        return None

    try:
        writer = imageio.get_writer(str(output_file), fps=fps)
        for img in images:
            writer.append_data(img)
        writer.close()
        logger.info(f"Animation saved: {output_file} ({len(images)} frames)")
        return output_file
    except Exception as e:
        logger.error(f"MP4 creation failed: {e} — trying GIF fallback")

    gif_path = output_file.with_suffix('.gif')
    try:
        imageio.mimsave(str(gif_path), images, fps=fps)
        logger.info(f"GIF animation saved: {gif_path}")
        return gif_path
    except Exception as e2:
        logger.error(f"GIF creation also failed: {e2}")
        return None
