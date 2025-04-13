"""
SHTC3 temperature and humidity sensor implementation.
"""

import ctypes
import time
from ctypes import byref, c_float, c_uint32
from pathlib import Path
from typing import Dict, Optional, Union

from .exceptions import ReadError
from .sensor_base import SensorBase


class SHTC3Sensor(SensorBase):
    """
    Class for handling the SHTC3 temperature and humidity sensor using the SHT4x driver.

    This class uses the following functions from the SHT4x library:
      - sht4x_init: Initializes the sensor with a given I²C address.
      - sht4x_measure_high_precision: Performs a high-precision measurement.
      - sht4x_measure_medium_precision: Performs a medium-precision measurement.
      - sht4x_measure_lowest_precision: Performs a low-precision measurement.
      - sht4x_serial_number: Reads out the sensor's unique serial number.
      - sht4x_soft_reset: Performs a soft reset of the sensor.

    The default I²C address is set to 0x44.

    Units:
      - Temperature in °C.
      - Relative humidity in %RH.
    """

    def __init__(self, lib_path: Path, i2c_address: int = 0x44) -> None:
        super().__init__(lib_path)
        self.i2c_address = i2c_address
        self._initialized: bool = False

    def initialize(self) -> None:
        """
        Initialize the sensor using sht4x_init with the specified I²C address.
        """
        self._lib.sht4x_init(self.i2c_address)
        self._initialized = True

    def read(
        self,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        mode: str = "high"
    ) -> Dict[str, float]:
        """
        Read temperature and relative humidity from the sensor.

        Parameters
        ----------
        temperature : Optional[float]
            Ignored in this sensor, included for API compatibility.
        humidity : Optional[float]
            Ignored in this sensor, included for API compatibility.
        mode : str, optional
            Measurement precision mode. Acceptable values are:
            "high" (default), "medium", or "lowest".

        Returns
        -------
        dict
            A dictionary with:
              - 'temperature': Temperature in °C.
              - 'relative_humidity': Relative humidity in %RH.

        Raises
        ------
        ReadError
            If the sensor is not initialized or if the measurement fails.
        ValueError
            If an invalid mode is provided.
        """
        if not self._initialized:
            raise ReadError("SHTC3", "Sensor not initialized", -1, {"operation": "read"})

        temp_val = c_float()
        hum_val = c_float()
        if mode == "high":
            ret = self._lib.sht4x_measure_high_precision(byref(temp_val), byref(hum_val))
        elif mode == "medium":
            ret = self._lib.sht4x_measure_medium_precision(byref(temp_val), byref(hum_val))
        elif mode == "lowest":
            ret = self._lib.sht4x_measure_lowest_precision(byref(temp_val), byref(hum_val))
        else:
            raise ValueError("Invalid mode. Choose 'high', 'medium', or 'lowest'.")
        if ret != 0:
            raise ReadError(
                "SHTC3",
                f"Failed to read temperature/humidity in {mode} precision mode",
                ret,
                {"operation": f"sht4x_measure_{mode}_precision"},
            )
        return {
            "temperature": temp_val.value,
            "relative_humidity": hum_val.value,
        }

    def get_info(self) -> Dict[str, Union[str, int]]:
        """
        Retrieve the sensor's serial number.

        Returns
        -------
        dict
            A dictionary with:
              - 'serial_number': The sensor serial number.

        Raises
        ------
        ReadError
            If the sensor is not initialized or if reading fails.
        """
        if not self._initialized:
            raise ReadError("SHTC3", "Sensor not initialized", -1, {"operation": "get_info"})
        serial_number = c_uint32()
        error = self._lib.sht4x_serial_number(byref(serial_number))
        if error != 0:
            raise ReadError("SHTC3", "Failed to retrieve serial number", error, {"operation": "sht4x_serial_number"})
        return {"serial_number": serial_number.value}

    def soft_reset(self) -> None:
        """
        Perform a soft reset of the sensor.
        A short delay is applied to allow the sensor to reboot.

        Raises
        ------
        ReadError
            If the reset command fails.
        """
        if not self._initialized:
            raise ReadError("SHTC3", "Sensor not initialized", -1, {"operation": "soft_reset"})
        ret = self._lib.sht4x_soft_reset()
        if ret != 0:
            raise ReadError("SHTC3", "Soft reset failed", ret, {"operation": "sht4x_soft_reset"})
        time.sleep(0.05)

    def sleep(self) -> None:
        """
        Put the sensor into sleep mode.

        Note
        ----
        The SHTC3 sensor does not support a dedicated sleep mode through the SHT4x driver.
        """
        pass

    def wake_up(self) -> None:
        """
        Wake up the sensor from sleep mode.

        Note
        ----
        The SHTC3 sensor does not support a dedicated wake-up function through the SHT4x driver.
        """
        pass
