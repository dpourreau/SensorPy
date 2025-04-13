"""
Sensor Manager for coordinating multiple Sensirion sensors.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Union

from .exceptions import InitializationError, ReadError
from .shtc3_sensor import SHTC3Sensor
from .sps30_sensor import SPS30Sensor
from .stc31c_sensor import STC31CSensor

# Configure logger
logger = logging.getLogger(__name__)


class SensorManager:
    """
    Class to manage all sensors.

    Initialization order:
      1. STC31-C: Requires I²C initialization, sensor address, and binary gas configuration.
      2. SHTC3: Provides temperature and humidity for compensating STC31-C.
      3. SPS30: Measures particulate matter via UART.

    Units:
      - STC31-C: CO₂ in ppm, temperature in °C.
      - SHTC3: Temperature in °C, relative humidity in %RH.
      - SPS30: Mass concentrations in µg/m³, number concentrations in #/cm³, particle size in µm.
    """

    def __init__(
        self,
        lib_path: Optional[Path] = None,
        co2_self_calibration: bool = False,
        enable_stc31c: bool = True,
        enable_shtc3: bool = True,
        enable_sps30: bool = True,
    ) -> None:
        # Provide a default library path if none is provided.
        if lib_path is None:
            lib_path = (
                Path(__file__).resolve().parent.parent.parent / "drivers_c" / "build"
            )

        # Ensure SHTC3 is enabled if STC31-C is enabled (dependency requirement)
        if enable_stc31c and not enable_shtc3:
            logger.error(
                "STC31C sensor requires SHTC3 data. Enabling SHTC3 sensor automatically."
            )
            enable_shtc3 = True

        # Store sensor activation flags
        self.enable_stc31c = enable_stc31c
        self.enable_shtc3 = enable_shtc3
        self.enable_sps30 = enable_sps30

        # Instantiate sensor classes based on activation flags
        self.stc31c: Optional[STC31CSensor] = (
            STC31CSensor(lib_path, self_calibration=co2_self_calibration)
            if enable_stc31c
            else None
        )
        self.shtc3: Optional[SHTC3Sensor] = SHTC3Sensor(lib_path) if enable_shtc3 else None
        self.sps30: Optional[SPS30Sensor] = SPS30Sensor(lib_path) if enable_sps30 else None

        try:
            if self.enable_stc31c:
                assert self.stc31c is not None
                self.stc31c.initialize()
            if self.enable_shtc3:
                assert self.shtc3 is not None
                self.shtc3.initialize()
            if self.enable_sps30:
                assert self.sps30 is not None
                self.sps30.initialize(auto_clean_days=4)
        except (InitializationError, ReadError) as e:
            self.shutdown()
            raise e

    def get_all_info(self) -> Dict[str, Dict[str, Union[str, int]]]:
        """
        Retrieve basic identification/firmware info from all enabled sensors.
        Returns a dictionary with keys for each enabled sensor:
          - "stc31c": Sensor info from the STC31-C (if enabled).
          - "shtc3": Sensor info from the SHTC3 (if enabled).
          - "sps30": Sensor info from the SPS30 (if enabled).
        """
        result: Dict[str, Dict[str, Union[str, int]]] = {}
        if self.enable_stc31c:
            assert self.stc31c is not None
            result["stc31c"] = self.stc31c.get_info()
        if self.enable_shtc3:
            assert self.shtc3 is not None
            result["shtc3"] = self.shtc3.get_info()
        if self.enable_sps30:
            assert self.sps30 is not None
            result["sps30"] = self.sps30.get_info()
        return result

    def read_all(self) -> Dict[str, Dict[str, float]]:
        """
        Read data from all enabled sensors, using SHTC3 data for compensation if both SHTC3 and STC31-C are enabled.

        The order of operations is:
          1. Read SHTC3 for temperature and relative humidity (if enabled).
          2. Use these values to read the STC31-C (CO₂ measurement) if both sensors are enabled.
          3. Read SPS30 for particulate matter data (if enabled).

        Returns a dictionary with keys for each enabled sensor:
          - "shtc3": Temperature and relative humidity (if enabled).
          - "stc31c": CO₂ concentration (ppm) and sensor temperature (°C) (if enabled).
          - "sps30": Particulate matter measurements (if enabled).
        """
        result: Dict[str, Dict[str, float]] = {}

        # Read SHTC3 first if enabled
        shtc3_data: Optional[Dict[str, float]] = None
        if self.enable_shtc3:
            assert self.shtc3 is not None
            shtc3_data = self.shtc3.read()
            result["shtc3"] = shtc3_data

        # Read STC31C if enabled (requires SHTC3 data)
        if self.enable_stc31c:
            assert self.stc31c is not None
            if shtc3_data:
                stc31c_data = self.stc31c.read(
                    temperature=shtc3_data["temperature"],
                    humidity=shtc3_data["relative_humidity"],
                )
                result["stc31c"] = stc31c_data
            else:
                logger.error("Cannot read STC31C without SHTC3 data. Skipping STC31C reading.")

        # Read SPS30 if enabled
        if self.enable_sps30:
            assert self.sps30 is not None
            result["sps30"] = self.sps30.read()

        return result

    def shutdown(self) -> None:
        """
        Shutdown all enabled sensors gracefully.

        For the SPS30 sensor, this involves stopping the measurement (if active)
        and closing the UART interface. Additional cleanup for other sensors can
        be added as needed.
        """
        logger.info("Shutting down all enabled sensors")

        # Try to stop SPS30 measurement if active and enabled
        if self.enable_sps30 and self.sps30 is not None:
            try:
                if self.sps30._measurement_started:
                    logger.debug("Stopping SPS30 measurement")
                    self.sps30.stop_measurement()
            except Exception as e:
                logger.warning("Failed to stop SPS30 measurement: %s", str(e))

            # Try to close SPS30 connection
            try:
                logger.debug("Closing SPS30 connection")
                self.sps30.close()
            except Exception as e:
                logger.warning("Failed to close SPS30 connection: %s", str(e))

        # Add shutdown procedures for other sensors if needed
        # Currently, STC31C and SHTC3 don't require special shutdown procedures

        logger.info("Sensor shutdown complete")

    def sleep_all(self) -> None:
        """
        Put all enabled sensors that support sleep mode into sleep mode.

        This method attempts to put each enabled sensor into sleep mode, skipping any
        sensors that don't support the operation. Exceptions from individual
        sensors are caught and logged, allowing the method to continue with
        other sensors.
        """
        # Try to put STC31C to sleep if enabled
        if self.enable_stc31c and self.stc31c is not None:
            try:
                self.stc31c.sleep()
            except NotImplementedError:
                logger.debug("STC31C sensor does not support sleep mode")
            except Exception as e:
                logger.warning("Failed to put STC31C to sleep: %s", str(e))

        # Try to put SHTC3 to sleep if enabled
        if self.enable_shtc3 and self.shtc3 is not None:
            try:
                self.shtc3.sleep()
            except NotImplementedError:
                logger.debug("SHTC3 sensor does not support sleep mode")
            except Exception as e:
                logger.warning("Failed to put SHTC3 to sleep: %s", str(e))

        # Try to put SPS30 to sleep if enabled
        if self.enable_sps30 and self.sps30 is not None:
            try:
                # SPS30 requires stopping measurement before sleeping
                if self.sps30._measurement_started:
                    self.sps30.stop_measurement()
                self.sps30.sleep()
            except NotImplementedError:
                logger.debug("SPS30 sensor does not support sleep mode")
            except Exception as e:
                logger.warning("Failed to put SPS30 to sleep: %s", str(e))

    def wake_up_all(self) -> None:
        """
        Wake up all enabled sensors that support wake-up functionality.

        This method attempts to wake up each enabled sensor from sleep mode, skipping any
        sensors that don't support the operation. Exceptions from individual
        sensors are caught and logged, allowing the method to continue with
        other sensors.
        """
        # Try to wake up STC31C if enabled
        if self.enable_stc31c and self.stc31c is not None:
            try:
                self.stc31c.wake_up()
            except NotImplementedError:
                logger.debug("STC31C sensor does not support wake-up")
            except Exception as e:
                logger.warning("Failed to wake up STC31C: %s", str(e))

        # Try to wake up SHTC3 if enabled
        if self.enable_shtc3 and self.shtc3 is not None:
            try:
                self.shtc3.wake_up()
            except NotImplementedError:
                logger.debug("SHTC3 sensor does not support wake-up")
            except Exception as e:
                logger.warning("Failed to wake up SHTC3: %s", str(e))

        # Try to wake up SPS30 if enabled
        if self.enable_sps30 and self.sps30 is not None:
            try:
                self.sps30.wake_up()
            except NotImplementedError:
                logger.debug("SPS30 sensor does not support wake-up")
            except Exception as e:
                logger.warning("Failed to wake up SPS30: %s", str(e))
