#!/usr/bin/env python3
"""
Potter - AI Text Processing Tool
Refactored main entry point using modular architecture
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Import after path setup
from core.service import PotterService  # noqa: E402
from utils.logging_config import setup_logging, get_logger  # noqa: E402

# Set up logging with rotation and proper configuration
setup_logging(
    level='INFO',
    console=True,
    file=True,
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5
)

logger = get_logger(__name__)


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