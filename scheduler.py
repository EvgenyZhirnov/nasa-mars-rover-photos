"""
Scheduler: registers and runs periodic background jobs.
start_schedulers() is idempotent — safe to call multiple times.
"""
import logging
import threading
import time
import schedule
from datetime import datetime

import config

logger = logging.getLogger(__name__)

_scheduler_started = False
_lock = threading.Lock()


def fetch_nasa_images_job():
    try:
        import nasa_api
        nasa_api.fetch_and_save_photos()
    except Exception as e:
        logger.error(f"fetch_nasa_images_job failed: {e}")


def update_apod_job():
    try:
        import nasa_apod
        nasa_apod.download_apod()
    except Exception as e:
        logger.error(f"update_apod_job failed: {e}")


def update_epic_photos_job():
    try:
        import nasa_epic
        nasa_epic.download_all_epic_photos()
    except Exception as e:
        logger.error(f"update_epic_photos_job failed: {e}")


def create_daily_animation_job():
    try:
        import animation_creator
        animation_creator.create_animation()
    except Exception as e:
        logger.error(f"create_daily_animation_job failed: {e}")


def send_telegram_animation_job():
    try:
        import telegram_bot
        telegram_bot.send_animation()
    except Exception as e:
        logger.error(f"send_telegram_animation_job failed: {e}")


def _run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_schedulers():
    """Register all jobs and start the background thread. Idempotent."""
    global _scheduler_started

    with _lock:
        if _scheduler_started:
            logger.info("Scheduler already running — skipping duplicate start")
            return
        _scheduler_started = True

    schedule.every(config.FETCH_INTERVAL_SECONDS).seconds.do(fetch_nasa_images_job)
    schedule.every().day.at(config.APOD_UPDATE_TIME).do(update_apod_job)
    schedule.every().day.at(config.EPIC_UPDATE_TIME).do(update_epic_photos_job)
    schedule.every().day.at(config.ANIMATION_CREATE_TIME).do(create_daily_animation_job)
    schedule.every().day.at(config.ANIMATION_SEND_TIME).do(send_telegram_animation_job)

    now = datetime.now().time()
    if now.hour > 16 or (now.hour == 16 and now.minute > 0):
        if not config.ANIMATION_MP4.exists() and not config.ANIMATION_GIF.exists():
            logger.info("Started after 16:00 with no animation — generating now")
            create_daily_animation_job()
            if now.hour > 16 or (now.hour == 16 and now.minute >= 5):
                send_telegram_animation_job()

    t = threading.Thread(target=_run_scheduler, daemon=True, name="scheduler")
    t.start()
    logger.info("Scheduler background thread started")
