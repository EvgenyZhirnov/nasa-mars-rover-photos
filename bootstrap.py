"""
Bootstrap: single place that wires everything together on startup.
Called once — from main.py when the process starts.
"""
import logging
import threading
import config

logger = logging.getLogger(__name__)
_lock = threading.Lock()
_background_thread = None


def ensure_directories():
    """Create all required data directories if they do not exist."""
    for directory in (config.NASA_IMAGES_DIR, config.NASA_APOD_DIR, config.NASA_EPIC_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    logger.info("Data directories ready")


def run_initial_sync():
    """Fetch fresh data from all NASA APIs on first startup."""
    import nasa_hub
    nasa_hub.prime()
    import nasa_api
    import nasa_apod
    import nasa_epic

    try:
        count = nasa_api.fetch_and_save_photos()
        logger.info(f"Initial Mars Rover fetch: {count} new photos")
    except Exception as e:
        logger.error(f"Initial Mars Rover fetch failed: {e}")

    try:
        path, _ = nasa_apod.download_apod()
        logger.info(f"Initial APOD download: {path or 'skipped (video or already present)'}")
    except Exception as e:
        logger.error(f"Initial APOD download failed: {e}")

    try:
        count, _ = nasa_epic.download_all_epic_photos()
        logger.info(f"Initial EPIC download: {count} photos")
    except Exception as e:
        logger.error(f"Initial EPIC download failed: {e}")


def start_services():
    """Start background scheduler and Telegram bot (if configured)."""
    from scheduler import start_schedulers
    start_schedulers()

    if config.TELEGRAM_BOT_TOKEN:
        try:
            from telegram_bot import TelegramBot
            bot = TelegramBot()
            bot.start()
            logger.info("Telegram bot started")
        except Exception as e:
            logger.error(f"Telegram bot failed to start: {e}")
    else:
        logger.info("Telegram bot token not set — skipping bot startup")


def _run_background_services():
    # Keep initial sync and scheduled jobs sequential to avoid duplicate writes.
    try:
        run_initial_sync()
    finally:
        start_services()


def bootstrap():
    """Prepare local storage and start one background thread per worker process."""
    global _background_thread
    with _lock:
        if _background_thread is not None:
            return _background_thread
        ensure_directories()
        import comments
        comments.init_db()
        _background_thread = threading.Thread(
            target=_run_background_services, daemon=True, name="nasa-bootstrap"
        )
        _background_thread.start()
    logger.info("Local storage ready; NASA sync continues in background")
    return _background_thread
