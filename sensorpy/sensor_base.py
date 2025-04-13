"""
Base sensor class for all Sensirion sensors.
"""

import ctypes
from pathlib import Path
from typing import Dict, Optional, Union


class SensorBase:
    """Base class for sensor handling."""

    def __init__(self, lib_path: Path) -> None:
        self.lib_path = lib_path
        # Load the shared C library containing all driver functions.
        # Adjust "libsensirion.so" if your shared library name differs.
        self._lib = ctypes.CDLL(str(lib_path / "libsensirion.so"))
        self._initialized = False
        self._sleeping = False

    def initialize(self) -> None:
        """Perform hardware or bus initialization for the sensor."""
        raise NotImplementedError

    def read(self, temperature: Optional[float] = None, humidity: Optional[float] = None) -> Dict[str, float]:
        """Perform a sensor measurement and return results."""
        raise NotImplementedError

    def get_info(self) -> Dict[str, Union[str, int]]:
        """
        Retrieve sensor-specific information such as serial numbers,
        firmware versions, product IDs, etc.
        """
        raise NotImplementedError

    def sleep(self) -> None:
        """
        Put the sensor into sleep mode to minimize power consumption.

        This is a base method that should be implemented by sensors that support
        sleep functionality. The implementation should handle the specific sleep
        mechanism for the sensor.

        Raises:
            NotImplementedError: If the sensor does not support sleep mode.
        """
        raise NotImplementedError("Sleep mode not supported by this sensor")

    def wake_up(self) -> None:
        """
        Wake up the sensor from sleep mode.

        This is a base method that should be implemented by sensors that support
        wake-up functionality. The implementation should handle the specific wake-up
        mechanism for the sensor.

        Raises:
            NotImplementedError: If the sensor does not support wake-up.
        """
        raise NotImplementedError("Wake-up not supported by this sensor")
