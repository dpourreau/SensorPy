"""
Sensirion Sensors Python Package

This package provides Python bindings for Sensirion sensors:
- STC31-C: CO2 concentration and temperature sensor
- SHTC3: Temperature and humidity sensor
- SPS30: Particulate matter sensor

The package uses ctypes to interface with the C drivers provided by Sensirion.
"""

import logging
from logging import NullHandler
from typing import Optional

from .exceptions import InitializationError, ReadError, SensorError
from .sensor_base import SensorBase
from .sensor_manager import SensorManager
from .shtc3_sensor import SHTC3Sensor
from .sps30_sensor import SPS30Sensor
from .stc31c_sensor import STC31CSensor


def setup_logging(
    level: int = logging.INFO,
    format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file: Optional[str] = None,
) -> None:
    """
    Configure logging for the Sensirion Sensors package.

    Args:
        level: The logging level (default: logging.INFO)
        format_str: The log message format string
        log_file: Optional file path to write logs to

    Example:
        >>> import sensorpy
        >>> sensorpy.setup_logging(level=logging.DEBUG)
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    formatter = logging.Formatter(format_str)

    # Add a console handler if not already present
    if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add a file handler if log_file is specified and not already present
    if log_file and not any(
        isinstance(handler, logging.FileHandler) and handler.baseFilename == log_file
        for handler in logger.handlers
    ):
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.debug("Logging initialized for Sensirion Sensors package")


__version__ = "0.1.0"
__all__ = [
    "SensorManager",
    "SensorBase",
    "STC31CSensor",
    "SHTC3Sensor",
    "SPS30Sensor",
    "SensorError",
    "InitializationError",
    "ReadError",
    "setup_logging",
]
