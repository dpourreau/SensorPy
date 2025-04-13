"""
STC31-C CO₂ sensor implementation.
"""

import ctypes
import time
from ctypes import POINTER, c_float, c_uint16, c_uint32, c_uint64
from pathlib import Path
from typing import Dict, Optional, Union

from .exceptions import InitializationError, ReadError
from .sensor_base import SensorBase


class STC31CSensor(SensorBase):
    """
    Class for handling the STC31-C CO₂ sensor (using stc3x driver functions).

    Important notes based on Sensirion's STC3x documentation:
      - I²C initialization via sensirion_i2c_hal_init.
      - I²C address is 0x29.
      - stc3x_set_binary_gas(19) configures the sensor for CO₂ in air (0–40 vol%).
      - The sensor requires periodic updates for temperature and humidity compensation.

    Units:
      - CO₂ concentration is returned in parts per million (ppm).
        (Conversion: 1 Vol% = 10,000 ppm)
      - Temperature is returned in degrees Celsius (°C).
    """

    def __init__(self, lib_path: Path, self_calibration: bool = False) -> None:
        super().__init__(lib_path)
        self._initialized: bool = False
        self._sleeping: bool = False
        self._enable_asc: bool = self_calibration

    def initialize(self) -> None:
        """
        Initialize the STC31-C sensor:

          1. Initialize the I²C bus.
          2. Call stc3x_init(0x29).
          3. Set binary gas configuration via stc3x_set_binary_gas(19).
          4. Enable or disable automatic self-calibration based on configuration.
        """
        ret = self._lib.sensirion_i2c_hal_init()
        if ret != 0:
            raise InitializationError(
                "STC31-C", "Failed to initialize I²C interface", ret, {"operation": "sensirion_i2c_hal_init"}
            )

        # stc3x_init returns void, so there's no error code to check.
        self._lib.stc3x_init(0x29)

        # Configure binary gas (19 corresponds to CO₂ in air for 0–40 vol%).
        ret = self._lib.stc3x_set_binary_gas(19)
        if ret != 0:
            raise InitializationError(
                "STC31-C", "Failed to set binary gas configuration", ret, {"operation": "stc3x_set_binary_gas", "gas_config": 19}
            )

        # Configure automatic self-calibration if requested
        if self._enable_asc:
            self.enable_automatic_self_calibration()
        else:
            self.disable_automatic_self_calibration()

        # Optional: wait a short time after writing commands.
        time.sleep(0.05)
        self._initialized = True
        self._sleeping = False

    def read(self, temperature: Optional[float] = None, humidity: Optional[float] = None) -> Dict[str, float]:
        """
        Read the CO₂ concentration with compensation for ambient temperature and relative humidity.

        Parameters
        ----------
        temperature : Optional[float]
            Ambient temperature in °C (required).
        humidity : Optional[float]
            Relative humidity in % (required).

        Returns
        -------
        dict
            Dictionary with:
              "co2_concentration": CO₂ concentration in ppm.
              "temperature": Sensor temperature reading in °C.

        Note
        ----
        The measurement command should not be triggered more than once per second.
        """
        if not self._initialized:
            raise ReadError("STC31-C", "Sensor not initialized", -1, {"operation": "read"})
        if temperature is None or humidity is None:
            raise ValueError("STC31CSensor.read() requires 'temperature' and 'humidity' values.")

        # Set compensation values using raw functions.
        error = self._lib.stc3x_set_relative_humidity(c_float(humidity))
        if error != 0:
            raise ReadError(
                "STC31-C",
                "Failed to set relative humidity for compensation",
                error,
                {"operation": "stc3x_set_relative_humidity", "humidity": humidity},
            )

        error = self._lib.stc3x_set_temperature(c_float(temperature))
        if error != 0:
            raise ReadError(
                "STC31-C",
                "Failed to set temperature for compensation",
                error,
                {"operation": "stc3x_set_temperature", "temperature": temperature},
            )

        co2_vol = c_float()
        temperature_out = c_float()
        ret = self._lib.stc3x_measure_gas_concentration(ctypes.byref(co2_vol), ctypes.byref(temperature_out))
        if ret != 0:
            raise ReadError("STC31-C", "Failed to read gas concentration", ret, {"operation": "stc3x_measure_gas_concentration"})

        # Convert from Vol% to ppm. (1 Vol% = 10,000 ppm)
        co2_ppm = co2_vol.value * 10000
        return {
            "co2_concentration": co2_ppm,
            "temperature": temperature_out.value,
        }

    def get_info(self) -> Dict[str, Union[str, int]]:
        """
        Retrieve product ID and serial number from the sensor.

        Returns
        -------
        dict
            Dictionary with keys:
              "product_id": <int>,
              "serial_number": <string>
        """
        product_id = c_uint32()
        serial_number = c_uint64()
        error = self._lib.stc3x_get_product_id(POINTER(c_uint32)(product_id), POINTER(c_uint64)(serial_number))
        if error != 0:
            raise ReadError("STC31-C", "Failed to retrieve product info", error, {"operation": "stc3x_get_product_id"})
        return {
            "product_id": product_id.value,
            "serial_number": f"{serial_number.value:X}",
        }

    def forced_recalibration(self, reference_concentration: int) -> None:
        """
        Perform forced recalibration using a known reference concentration (in vol%).

        Parameters
        ----------
        reference_concentration : int
            The reference concentration in vol%.
        """
        ret = self._lib.stc3x_forced_recalibration(c_uint16(reference_concentration))
        if ret != 0:
            raise ReadError(
                "STC31-C",
                "Forced recalibration failed",
                ret,
                {"operation": "stc3x_forced_recalibration", "reference": reference_concentration},
            )

    def enable_automatic_self_calibration(self) -> None:
        """
        Enable automatic self-calibration (ASC).
        """
        ret = self._lib.stc3x_enable_automatic_self_calibration()
        if ret != 0:
            raise ReadError(
                "STC31-C",
                "Enabling automatic self-calibration failed",
                ret,
                {"operation": "stc3x_enable_automatic_self_calibration"},
            )
        time.sleep(0.01)

    def disable_automatic_self_calibration(self) -> None:
        """
        Disable automatic self-calibration (ASC).
        """
        ret = self._lib.stc3x_disable_automatic_self_calibration()
        if ret != 0:
            raise ReadError(
                "STC31-C",
                "Disabling automatic self-calibration failed",
                ret,
                {"operation": "stc3x_disable_automatic_self_calibration"},
            )
        time.sleep(0.01)

    def sleep(self) -> None:
        """
        Put the sensor into sleep mode. In sleep mode the sensor consumes minimal power.
        Must be called when the sensor is idle.
        """
        ret = self._lib.stc3x_enter_sleep_mode()
        if ret != 0:
            raise ReadError("STC31-C", "Entering sleep mode failed", ret, {"operation": "stc3x_enter_sleep_mode"})
        self._sleeping = True

    def wake_up(self) -> None:
        """
        Wake the sensor from sleep mode.
        """
        ret = self._lib.stc3x_exit_sleep_mode()
        if ret != 0:
            raise ReadError("STC31-C", "Exiting sleep mode failed", ret, {"operation": "stc3x_exit_sleep_mode"})
        self._sleeping = False
