"""
Main entry point for the NASA Mars Rover Photos application.
"""
import os
import logging
import atexit
from web_server import app
from scheduler import start_schedulers
from nasa_api import fetch_and_save_photos
from nasa_apod import download_apod
from nasa_epic import download_all_epic_photos

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
def ensure_directories():
    """Ensure all required directories exist."""
    try:
        os.makedirs('data/nasa_images', exist_ok=True)
        os.makedirs('data/nasa_apod', exist_ok=True)
        os.makedirs('data/nasa_epic', exist_ok=True)
        logger.info("Data directories created successfully")
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        raise

def shutdown_hook():
    """Cleanup function to be called when the application exits."""
    logger.info("Application shutting down...")

def main():
    # Ensure required directories exist
    ensure_directories()

    # Register shutdown hook
    atexit.register(shutdown_hook)

    # Start the schedulers in a separate thread
    start_schedulers()

    try:
        # Fetch Mars Rover images on startup
        rover_result = fetch_and_save_photos()
        logger.info(f"Initial fetch of Mars Rover photos: {rover_result} new images saved")

        # Download APOD on startup
        apod_result = download_apod()
        if apod_result[0]:
            logger.info(f"Initial download of APOD: {apod_result[0]}")
        else:
            logger.warning("Failed to download initial APOD")

        # Download EPIC photos on startup
        epic_count, epic_paths = download_all_epic_photos()
        if epic_count > 0:
            logger.info(f"Initial download of EPIC photos: {epic_count} photos saved")
        else:
            logger.warning("Failed to download initial EPIC photos")
    except Exception as e:
        logger.error(f"Error during startup tasks: {e}")

    # Start the Flask application
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    # Initialize and start telegram bot
    from telegram_bot import TelegramBot
    bot = TelegramBot()
    bot.start()

    main()