"""
Scheduler module for periodic tasks.
"""
import logging
import schedule
import threading
import time
from datetime import datetime

# Import other modules
import nasa_api
import nasa_epic
import nasa_apod
import animation_creator
import telegram_bot

logger = logging.getLogger(__name__)

def fetch_nasa_images_job():
    """Job to fetch NASA Mars Rover images."""
    logger.info("Running scheduled job: Fetch NASA Mars Rover images")
    try:
        nasa_api.fetch_and_save_photos()
    except Exception as e:
        logger.error(f"Error in fetch_nasa_images_job: {e}")

def update_apod_job():
    """Job to update NASA's Astronomy Picture of the Day."""
    logger.info("Running scheduled job: Update APOD")
    try:
        nasa_apod.download_apod()
    except Exception as e:
        logger.error(f"Error in update_apod_job: {e}")

def update_epic_photos_job():
    """Job to update NASA's EPIC Earth photos."""
    logger.info("Running scheduled job: Update EPIC photos")
    try:
        nasa_epic.download_all_epic_photos()
    except Exception as e:
        logger.error(f"Error in update_epic_photos_job: {e}")
        
def create_daily_animation_job():
    """Job to create a daily animation from saved images."""
    logger.info("Running scheduled job: Create daily animation")
    try:
        animation_creator.create_animation()
    except Exception as e:
        logger.error(f"Error in create_daily_animation_job: {e}")

def send_telegram_animation_job():
    """Job to send the latest animation via Telegram."""
    logger.info("Running scheduled job: Send Telegram animation")
    try:
        telegram_bot.send_animation()
    except Exception as e:
        logger.error(f"Error in send_telegram_animation_job: {e}")

def run_scheduler():
    """Run the scheduler in an infinite loop."""
    logger.info("Starting scheduler")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_schedulers():
    """Set up and start all scheduled jobs."""
    # Schedule fetching NASA images every 2.4 minutes (25 times per hour)
    schedule.every(2.4 * 60).seconds.do(fetch_nasa_images_job)
    
    # Schedule updating APOD image daily at 00:30
    schedule.every().day.at("00:30").do(update_apod_job)
    
    # Schedule updating EPIC photos daily at 01:00
    schedule.every().day.at("01:00").do(update_epic_photos_job)
    
    # Schedule creating the daily animation at 16:00
    schedule.every().day.at("16:00").do(create_daily_animation_job)
    
    # Schedule sending the Telegram animation at 16:05
    schedule.every().day.at("16:05").do(send_telegram_animation_job)
    
    # Run initial fetch jobs at startup
    fetch_nasa_images_job()
    update_apod_job()
    update_epic_photos_job()
    
    # Check if we missed the animation job for today
    current_time = datetime.now().time()
    if current_time.hour > 16 or (current_time.hour == 16 and current_time.minute > 0):
        logger.info("First run after 16:00, checking if animation exists")
        
        # Only run if animation doesn't exist yet
        import os
        if not os.path.exists("/data/nasa_animation.mp4") and not os.path.exists("/data/nasa_animation.gif"):
            logger.info("Running animation creation job now")
            create_daily_animation_job()
            
            # If after 16:05, also send the telegram animation
            if current_time.hour > 16 or (current_time.hour == 16 and current_time.minute >= 5):
                logger.info("Running Telegram send job now")
                send_telegram_animation_job()
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Scheduler started in background thread")
