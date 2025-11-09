#!/usr/bin/env python3
"""
ADZ Daemon - Background task processor for ZeroTouch Atlas
Watches ~/dropzone/tasks/ for new task files and processes them automatically
"""

import sys
import logging
from pathlib import Path

# Add lib directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.claude' / 'logs' / 'adz_daemon.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        from agentic_dropzone import AgenticDropZone

        logger.info("🚀 Initializing ADZ Daemon...")

        # Create and start ADZ
        adz = AgenticDropZone()
        adz.start()  # This runs forever until Ctrl+C

    except KeyboardInterrupt:
        logger.info("\n🛑 ADZ Daemon stopped by user")
    except Exception as e:
        logger.error(f"❌ ADZ Daemon error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
