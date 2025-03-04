import logging
import sys

def configure_logging(level=logging.INFO):
    """Configure logging for the application."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# Set up default logging with WARNING level
# CLI will override this based on verbosity
configure_logging(logging.WARNING) 