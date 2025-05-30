#!/usr/bin/env python3
"""
Potter - AI Text Processing Tool
Refactored main entry point using modular architecture
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Import the main service
from core.service import PotterService

# Configure logging - use appropriate location for app bundle vs development
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle - log to user's home directory
    log_path = Path.home() / 'Library' / 'Logs' / 'potter.log'
else:
    # Running from source - log to project directory
    log_path = src_path / 'potter.log'

# Ensure log directory exists
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for Potter"""
    try:
        logger.info("=" * 50)
        logger.info("🎭 Potter - AI Text Processing Tool")
        logger.info("Starting up...")
        logger.info("=" * 50)
        
        # Create and start the service
        service = PotterService()
        success = service.start()
        
        if not success:
            logger.error("Failed to start Potter service")
            return 1
        
        logger.info("Potter service finished")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Potter interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 