"""
SPS30 particulate matter sensor implementation.
"""

import ctypes
import time
from ctypes import c_char, c_uint8
from pathlib import Path
from typing import Dict, Optional, Union

from .exceptions import InitializationError, ReadError
from .sensor_base import SensorBase
from .structures import SPS30_Measurement, SPS30_VersionInfo


class SPS30Sensor(SensorBase):
    """
    Class for handling the SPS30 particulate matter sensor.

    Features:
      - Initialization (open UART, probe sensor, read version/serial, set auto-clean interval, start measurement)
      - Reading measurements (only when measurement is active)
      - Stopping measurement (required before sleep or shutdown)
      - Sleep / wake support (firmware ≥ 2.0)
      - Manual fan cleaning and auto-cleaning interval get/set
      - Sensor reset and closing the UART

    Units:
      - Mass concentrations: in µg/m³.
      - Number concentrations: in counts per cubic centimeter (#/cm³).
      - Typical particle size: in micrometers (µm).
    """

    SPS30_MAX_SERIAL_LEN = 32

    def __init__(self, lib_path: Path) -> None:
        super().__init__(lib_path)
        self.version_info: Optional[SPS30_VersionInfo] = None
        self.serial_number: str = "Unknown"
        # Internal state flags to track prerequisites.
        self._initialized: bool = False
        self._uart_open: bool = False
        self._measurement_started: bool = False
        self._sleeping: bool = False

    def initialize(self, auto_clean_days: int = 4) -> None:
        """
        Initialize the SPS30 sensor for measurement:
          1) Open the UART interface.
          2) Probe the sensor.
          3) Read version info (firmware/hardware/SHDLC).
          4) Read the serial number.
          5) Optionally set the auto-cleaning interval (in days).
          6) Start measurement.
          7) Wait ~1.1s for data readiness.

        Parameters
        ----------
        auto_clean_days : int
            The desired auto-cleaning interval in days.
        """
        # 1) Open UART
        ret = self._lib.sensirion_uart_open()
        if ret != 0:
            raise InitializationError("SPS30", "Failed to initialize UART", ret, {"operation": "sensirion_uart_open"})
        self._uart_open = True

        # 2) Probe the sensor
        ret = self._lib.sps30_probe()
        if ret != 0:
            raise InitializationError("SPS30", "Failed to probe SPS30 sensor", ret, {"operation": "sps30_probe"})

        # 3) Read version info
        version_info = SPS30_VersionInfo()
        ret = self._lib.sps30_read_version(ctypes.byref(version_info))
        if ret == 0:
            self.version_info = version_info
        else:
            raise ReadError("SPS30", "Failed to retrieve version info", ret, {"operation": "sps30_read_version"})

        # 4) Read the serial number
        serial_buffer = (c_char * self.SPS30_MAX_SERIAL_LEN)()
        ret = self._lib.sps30_get_serial(serial_buffer)
        if ret == 0:
            self.serial_number = serial_buffer.value.decode()
        else:
            raise ReadError("SPS30", "Failed to retrieve serial number", ret, {"operation": "sps30_get_serial"})

        # 5) Set the auto-cleaning interval in days
        ret = self._lib.sps30_set_fan_auto_cleaning_interval_days(c_uint8(auto_clean_days))
        if ret != 0:
            raise ReadError(
                "SPS30",
                f"Could not set auto-clean interval to {auto_clean_days} day(s)",
                ret,
                {"operation": "sps30_set_fan_auto_cleaning_interval_days"},
            )

        # 6) Start measurement
        ret = self._lib.sps30_start_measurement()
        if ret != 0:
            raise InitializationError("SPS30", "Failed to start measurements", ret, {"operation": "sps30_start_measurement"})
        self._measurement_started = True

        # 7) Wait ~1.1s for sensor to produce first measurement data
        time.sleep(1.1)
        self._initialized = True
        self._sleeping = False

    def stop_measurement(self) -> None:
        """
        Stop measuring. The sensor enters idle mode.
        This must be called before invoking sleep() or shutting down.
        """
        if not self._measurement_started:
            raise ReadError(
                "SPS30", "Cannot stop measurement: measurement not started", -1, {"operation": "sps30_stop_measurement"}
            )
        ret = self._lib.sps30_stop_measurement()
        if ret != 0:
            raise ReadError("SPS30", "Stopping measurement failed", ret, {"operation": "sps30_stop_measurement"})
        self._measurement_started = False

    def read(self, temperature: Optional[float] = None, humidity: Optional[float] = None) -> Dict[str, float]:
        """
        Read particulate matter measurements from the SPS30 sensor.

        The sensor must be in measurement mode (i.e., initialize() has been called and measurement is active).

        Returns
        -------
        dict
            Dictionary containing particulate matter measurements with keys:
              "pm1.0", "pm2.5", "pm4.0", "pm10.0",
              "nc0.5", "nc1.0", "nc2.5", "nc4.0", "nc10.0",
              "typical_particle_size".

        Raises
        ------
        ReadError
            If the sensor is not properly initialized or if reading fails.
        """
        if not self._initialized or not self._measurement_started:
            raise ReadError(
                "SPS30", "Cannot read data: sensor not properly initialized or measurement not started", -1, {"operation": "read"}
            )

        measurement = SPS30_Measurement()
        ret = self._lib.sps30_read_measurement(ctypes.byref(measurement))

        if ret < 0:
            # sps30_read_measurement returns negative on error
            if ret == -1:  # SPS30_ERR_NOT_ENOUGH_DATA
                raise ReadError(
                    "SPS30",
                    "Not enough data available (the sensor needs more time).",
                    ret,
                    {"operation": "sps30_read_measurement"},
                )
            else:
                raise ReadError("SPS30", "Failed to read particulate matter data", ret, {"operation": "sps30_read_measurement"})
        return {
            "pm1.0": measurement.mc_1p0,
            "pm2.5": measurement.mc_2p5,
            "pm4.0": measurement.mc_4p0,
            "pm10.0": measurement.mc_10p0,
            "nc0.5": measurement.nc_0p5,
            "nc1.0": measurement.nc_1p0,
            "nc2.5": measurement.nc_2p5,
            "nc4.0": measurement.nc_4p0,
            "nc10.0": measurement.nc_10p0,
            "typical_particle_size": measurement.typical_particle_size,
        }

    def sleep(self) -> None:
        """
        Enter sleep mode with minimum power consumption (firmware ≥ 2.0 only).

        Must be called only when the sensor is in idle mode (i.e., after stop_measurement()).
        """
        if self.version_info is None or self.version_info.firmware_major < 2:
            return  # Sleep not supported on older firmware
        if not self._initialized:
            raise ReadError("SPS30", "Sensor not initialized", -1, {"operation": "sleep"})
        if self._measurement_started:
            raise ReadError("SPS30", "Stop measurement before sleeping", -1, {"operation": "sleep"})

        ret = self._lib.sps30_sleep()
        if ret != 0:
            raise ReadError("SPS30", "Entering sleep failed", ret, {"operation": "sps30_sleep"})
        self._sleeping = True

    def wake_up(self) -> None:
        """
        Wake up from sleep mode (firmware ≥ 2.0 only).

        Must be in sleep mode for this to succeed.
        """
        if self.version_info is None or self.version_info.firmware_major < 2:
            return  # Wake-up not supported on older firmware
        if not self._initialized:
            raise ReadError("SPS30", "Sensor not initialized", -1, {"operation": "wake_up"})
        if not self._sleeping:
            raise ReadError("SPS30", "Sensor is not sleeping", -1, {"operation": "wake_up"})
        ret = self._lib.sps30_wake_up()
        if ret != 0:
            raise ReadError("SPS30", "Waking up from sleep failed", ret, {"operation": "sps30_wake_up"})
        self._sleeping = False

    def start_manual_fan_cleaning(self) -> None:
        """
        Immediately trigger the fan cleaning procedure.
        Must be called when measurement is active.
        """
        if not self._measurement_started:
            raise ReadError(
                "SPS30",
                "Cannot perform manual fan cleaning: measurement not started",
                -1,
                {"operation": "sps30_start_manual_fan_cleaning"},
            )
        ret = self._lib.sps30_start_manual_fan_cleaning()
        if ret != 0:
            raise ReadError("SPS30", "Manual fan cleaning failed", ret, {"operation": "sps30_start_manual_fan_cleaning"})

    def set_fan_auto_cleaning_interval_days(self, days: int) -> None:
        """
        Set the fan's auto-cleaning interval in days.
        """
        ret = self._lib.sps30_set_fan_auto_cleaning_interval_days(c_uint8(days))
        if ret != 0:
            raise ReadError(
                "SPS30",
                f"Failed to set auto-cleaning interval to {days} day(s)",
                ret,
                {"operation": "sps30_set_fan_auto_cleaning_interval_days"},
            )

    def get_fan_auto_cleaning_interval_days(self) -> int:
        """
        Retrieve the current fan auto-cleaning interval in days.
        """
        interval_days = c_uint8()
        ret = self._lib.sps30_get_fan_auto_cleaning_interval_days(ctypes.byref(interval_days))
        if ret != 0:
            raise ReadError(
                "SPS30",
                "Failed to get auto-cleaning interval (days)",
                ret,
                {"operation": "sps30_get_fan_auto_cleaning_interval_days"},
            )
        return interval_days.value

    def reset(self) -> None:
        """
        Reset the SPS30 sensor.
        """
        ret = self._lib.sps30_reset()
        if ret != 0:
            raise ReadError("SPS30", "Failed to reset sensor", ret, {"operation": "sps30_reset"})

    def close(self) -> None:
        """
        Close the UART interface.
        """
        ret = self._lib.sensirion_uart_close()
        if ret != 0:
            raise ReadError("SPS30", "Failed to close UART", ret, {"operation": "sensirion_uart_close"})
        self._uart_open = False

    def get_info(self) -> Dict[str, Union[str, int]]:
        """
        Return basic sensor information gathered during initialization.
        """
        info: Dict[str, Union[str, int]] = {}
        if self.version_info is not None:
            info["firmware_version"] = f"{self.version_info.firmware_major}." f"{self.version_info.firmware_minor}"
            info["hardware_revision"] = self.version_info.hardware_revision
            info["shdlc_version"] = f"{self.version_info.shdlc_major}." f"{self.version_info.shdlc_minor}"
        else:
            info["firmware_version"] = "Unknown"
            info["hardware_revision"] = -1
            info["shdlc_version"] = "Unknown"

        info["serial_number"] = self.serial_number
        return info
