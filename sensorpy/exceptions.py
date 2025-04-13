"""
Custom exceptions for the Sensirion sensors package.
"""

from typing import Dict, Optional, Union


class SensorError(Exception):
    """Base exception for all sensor-related errors."""

    def __init__(
        self,
        sensor_name: str,
        message: str,
        error_code: Optional[int] = None,
        details: Optional[Dict[str, Union[str, int, float]]] = None,
    ):
        self.sensor_name = sensor_name
        self.error_code = error_code
        self.details = details or {}

        error_msg = f"[{sensor_name}] {message}"
        if error_code is not None:
            error_msg += f" (Error code: {error_code})"

        if details:
            error_msg += "\nDetails:"
            for key, value in details.items():
                error_msg += f"\n  {key}: {value}"

        super().__init__(error_msg)


class InitializationError(SensorError):
    """Raised when sensor initialization fails."""

    def __init__(
        self,
        sensor_name: str,
        message: str = "Failed to initialize sensor",
        error_code: Optional[int] = None,
        details: Optional[Dict[str, Union[str, int, float]]] = None,
    ):
        super().__init__(sensor_name, message, error_code, details)


class ReadError(SensorError):
    """Raised when reading from a sensor fails."""

    def __init__(
        self,
        sensor_name: str,
        message: str = "Failed to read sensor data",
        error_code: Optional[int] = None,
        details: Optional[Dict[str, Union[str, int, float]]] = None,
    ):
        super().__init__(sensor_name, message, error_code, details)
