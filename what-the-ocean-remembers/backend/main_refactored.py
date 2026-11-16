"""
Main entry point for Between Signals backend.

Initializes logging, loads configuration, and starts the communication server.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent))

from communication_refactored import create_communication_server


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('between_signals.log')
        ]
    )


def main() -> None:
    """Main entry point."""
    print("\n" + "=" * 60)
    print("BETWEEN SIGNALS - Backend Server")
    print("=" * 60 + "\n")

    # Setup logging
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Starting Between Signals backend server...")

    try:
        # Create and start the communication system
        router, server = create_communication_server(backend_port=8000)
        
        logger.info("Communication system initialized")
        logger.info("Listening for OSC messages on port 8000")
        logger.info("\nUsage:")
        logger.info("  - Run environment_a_test.py to listen on port 7001")
        logger.info("  - Run environment_b_test.py to listen on port 7002")
        logger.info("  - Run test_sender.py to send test messages")
        logger.info("  - Or use send_message.py to send manual messages\n")
        logger.info("Press Ctrl+C to stop.\n")

        # Start server (blocks until stopped)
        server.start()

    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
