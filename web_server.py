"""BookEase Web Server Entry Point."""

import sys
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("BookEase.Web")

# Initialize database
logger.info("Initializing BookEase database...")
from src.database.connection import init_db
init_db()

# Create Flask app (module-level for gunicorn: gunicorn web_server:app)
from web.app import create_app
from web.config import WebConfig

app = create_app(WebConfig)


def main():
    """Run the development server directly."""
    logger.info("Starting BookEase web server (dev mode)...")
    app.run(
        host=WebConfig.WEB_HOST,
        port=WebConfig.WEB_PORT,
        debug=WebConfig.DEBUG,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()
