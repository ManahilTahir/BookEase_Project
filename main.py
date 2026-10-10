"""BookEase Entry Point."""

import sys
import logging
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.database.connection import init_db
from src.ui.app import launch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("BookEase")


def main():
    """Start BookEase Application."""
    logger.info("Initializing BookEase Database and Workspace...")
    init_db()
    logger.info("Launching BookEase UI...")
    launch()


if __name__ == "__main__":
    main()
