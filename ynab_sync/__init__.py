import logging

__version__ = "0.1.0"

# Import cli after setting version to avoid circular imports
from .cli import cli 