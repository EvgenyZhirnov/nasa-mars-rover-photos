"""
Entry point. Runs bootstrap then hands off to Gunicorn (or Flask dev server).
"""
import logging
import atexit

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)s %(levelname)s %(message)s'
)

import bootstrap
bootstrap.bootstrap()

from web_server import app  # noqa: E402 — import after bootstrap

atexit.register(lambda: logging.getLogger(__name__).info("Application shutting down"))

if __name__ == "__main__":
    import config
    app.run(host=config.HOST, port=config.PORT, debug=False)
