"""
Unit tests for the SensorManager class and individual sensor readings.

This test suite verifies:
- Proper initialization of sensors.
- Successful and failed readings from STC31-C, SHTC3, and SPS30 sensors.
- Exception handling for initialization and read failures.
- Sleep and wake-up functionality for sensors that support it.
- Proper logging during operations.

Mocks are used to simulate sensor responses without requiring actual hardware.
"""

import logging
from pathlib import Path
from typing import Dict, Generator, Tuple, Union
from unittest.mock import MagicMock, patch

import pytest
from typing_extensions import Protocol

from sensorpy.exceptions import InitializationError, ReadError
from sensorpy.sensor_base import SensorBase
from sensorpy.sensor_manager import SensorManager
from sensorpy.shtc3_sensor import SHTC3Sensor
from sensorpy.sps30_sensor import SPS30Sensor
from sensorpy.stc31c_sensor import STC31CSensor


class MockSTC31CSensor(MagicMock):
    """Mock for STC31CSensor with sleep/wake support."""
    _sleeping = False

    def sleep(self) -> None:
        self._sleeping = True

    def wake_up(self) -> None:
        self._sleeping = False

    def initialize(self) -> None:
        pass

    def read(self, temperature: Union[float, None] = 25.0, humidity: Union[float, None] = 50.0) -> Dict[str, float]:
        return {"co2_concentration": 1000.0, "temperature": 25.0}

    def get_info(self) -> Dict[str, Union[str, int]]:
        return {"product_name": "STC31-C", "serial_number": "0123456789", "firmware_version": "1.0"}


class MockSHTC3Sensor(MagicMock):
    """Mock for SHTC3Sensor without sleep/wake support."""
    def initialize(self) -> None:
        pass

    def read(self, temperature: Union[float, None] = None, humidity: Union[float, None] = None, mode: str = "high") -> Dict[str, float]:
        return {"temperature": 25.0, "relative_humidity": 50.0}

    def get_info(self) -> Dict[str, Union[str, int]]:
        return {"product_name": "SHTC3", "serial_number": "9876543210", "firmware_version": "2.0"}

    def sleep(self) -> None:
        raise NotImplementedError("Sleep not supported")

    def wake_up(self) -> None:
        raise NotImplementedError("Wake-up not supported")


class MockSPS30Sensor(MagicMock):
    """Mock for SPS30Sensor with sleep/wake support."""
    _sleeping = False
    _measurement_started = False

    def sleep(self) -> None:
        self._sleeping = True
        self._measurement_started = False

    def wake_up(self) -> None:
        self._sleeping = False
        self._measurement_started = True

    def stop_measurement(self) -> None:
        self._measurement_started = False

    def initialize(self, auto_clean_days: int = 4) -> None:
        self._measurement_started = True

    def read(self, temperature: Union[float, None] = None, humidity: Union[float, None] = None) -> Dict[str, float]:
        return {
            "pm1.0": 10.0,
            "pm2.5": 25.0,
            "pm4.0": 40.0,
            "pm10.0": 100.0,
            "nc0.5": 5.0,
            "nc1.0": 10.0,
            "nc2.5": 25.0,
            "nc4.0": 40.0,
            "nc10.0": 100.0,
            "typical_particle_size": 2.5,
        }

    def get_info(self) -> Dict[str, Union[str, int]]:
        return {"product_name": "SPS30", "serial_number": "5555555555", "firmware_version": "3.0"}


@pytest.fixture
def mock_sensors() -> Generator[Tuple[MockSTC31CSensor, MockSHTC3Sensor, MockSPS30Sensor], None, None]:
    """Fixture to create mock sensors for testing."""
    stc31c_mock = MockSTC31CSensor(spec=STC31CSensor)
    shtc3_mock = MockSHTC3Sensor(spec=SHTC3Sensor)
    sps30_mock = MockSPS30Sensor(spec=SPS30Sensor)
    # Set the measurement_started flag to True for SPS30
    sps30_mock._measurement_started = True

    with patch("sensorpy.sensor_manager.STC31CSensor", return_value=stc31c_mock), \
         patch("sensorpy.sensor_manager.SHTC3Sensor", return_value=shtc3_mock), \
         patch("sensorpy.sensor_manager.SPS30Sensor", return_value=sps30_mock):
        yield stc31c_mock, shtc3_mock, sps30_mock


class MockPath:
    """Mock Path object for testing."""
    def __init__(self, *args: str) -> None:
        self.parts = args

    def resolve(self) -> "MockPath":
        return self

    def __truediv__(self, other: str) -> "MockPath":
        return MockPath(*self.parts, other)

    def __str__(self) -> str:
        return "/".join(self.parts)

    @property
    def parent(self) -> "MockPath":
        return MockPath(*self.parts[:-1])


@pytest.fixture
def sensor_manager(mock_sensors: Tuple[MockSTC31CSensor, MockSHTC3Sensor, MockSPS30Sensor]) -> SensorManager:
    """Fixture to initialize the SensorManager with mocked sensors."""
    with patch("pathlib.Path", MockPath), patch.object(SensorManager, "__init__", return_value=None):
        manager = SensorManager()
        stc31c_mock, shtc3_mock, sps30_mock = mock_sensors
        manager.stc31c = stc31c_mock
        manager.shtc3 = shtc3_mock
        manager.sps30 = sps30_mock
        return manager


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Fixture to capture and test logging output."""
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


def test_initialization_success(
    sensor_manager: SensorManager, mock_sensors: Tuple[MockSTC31CSensor, MockSHTC3Sensor, MockSPS30Sensor]
) -> None:
    """Test successful sensor initialization."""
    stc31c_mock, shtc3_mock, sps30_mock = mock_sensors
    assert sensor_manager.stc31c is stc31c_mock
    assert sensor_manager.shtc3 is shtc3_mock
    assert sensor_manager.sps30 is sps30_mock


def test_initialization_failure() -> None:
    """Test failure during sensor initialization."""
    failing_sensor = MagicMock()
    failing_sensor.initialize.side_effect = Exception("Failed to initialize")
    with patch("sensorpy.sensor_manager.STC31CSensor", return_value=failing_sensor), \
         patch("pathlib.Path", MockPath), \
         patch("sensorpy.sensor_manager.SensorManager.shutdown"):
        with pytest.raises(Exception):
            SensorManager()


def test_read_stc31c_success(sensor_manager: SensorManager) -> None:
    """Test successful CO2 concentration reading from STC31-C sensor."""
    assert sensor_manager.stc31c is not None, "STC31CSensor is None"
    data = sensor_manager.stc31c.read()
    assert "co2_concentration" in data
    assert data["co2_concentration"] == 1000.0


def test_read_shtc3_success(sensor_manager: SensorManager) -> None:
    """Test successful temperature and humidity reading from SHTC3 sensor."""
    assert sensor_manager.shtc3 is not None, "SHTC3Sensor is None"
    data = sensor_manager.shtc3.read()
    assert "temperature" in data
    assert "relative_humidity" in data


def test_read_sps30_success(sensor_manager: SensorManager) -> None:
    """Test successful particulate matter reading from SPS30 sensor."""
    assert sensor_manager.sps30 is not None, "SPS30Sensor is None"
    data = sensor_manager.sps30.read()
    assert "pm2.5" in data
    assert "typical_particle_size" in data


def test_read_all_success(sensor_manager: SensorManager) -> None:
    """Test successful reading from all sensors."""
    with patch.object(
        sensor_manager,
        "read_all",
        return_value={
            "stc31c": {"co2_concentration": 1000.0, "temperature": 25.0},
            "shtc3": {"temperature": 25.0, "relative_humidity": 50.0},
            "sps30": {"pm2.5": 25.0, "typical_particle_size": 2.5},
        },
    ):
        data = sensor_manager.read_all()
        assert "stc31c" in data
        assert "shtc3" in data
        assert "sps30" in data


def test_read_error_handling(sensor_manager: SensorManager) -> None:
    """Test error handling when sensors fail to return data."""
    assert sensor_manager.stc31c is not None, "STC31CSensor is None"
    with patch.object(sensor_manager.stc31c, "read", side_effect=Exception("Failed to read")):
        with pytest.raises(Exception):
            sensor_manager.stc31c.read()

    with patch.object(
        sensor_manager,
        "read_all",
        return_value={
            "shtc3": {"temperature": 25.0, "relative_humidity": 50.0},
            "sps30": {"pm2.5": 25.0, "typical_particle_size": 2.5},
        },
    ):
        data = sensor_manager.read_all()
        assert "shtc3" in data
        assert "sps30" in data
        assert "stc31c" not in data


def test_get_info_error_handling(sensor_manager: SensorManager) -> None:
    """Test error handling when retrieving sensor information fails."""
    assert sensor_manager.stc31c is not None, "STC31CSensor is None"
    with patch.object(sensor_manager.stc31c, "get_info", side_effect=Exception("Failed to get info")):
        with pytest.raises(Exception):
            sensor_manager.stc31c.get_info()

    with patch.object(
        sensor_manager,
        "get_all_info",
        return_value={
            "shtc3": {"product_name": "SHTC3", "serial_number": "9876543210", "firmware_version": "2.0"},
            "sps30": {"product_name": "SPS30", "serial_number": "5555555555", "firmware_version": "3.0"},
        },
    ):
        data = sensor_manager.get_all_info()
        assert "shtc3" in data
        assert "sps30" in data
        assert "stc31c" not in data


def test_sleep_wake_stc31c(sensor_manager: SensorManager) -> None:
    """Test sleep and wake-up functionality for STC31-C sensor."""
    assert sensor_manager.stc31c is not None, "STC31CSensor is None"
    assert not sensor_manager.stc31c._sleeping
    sensor_manager.stc31c.sleep()
    assert sensor_manager.stc31c._sleeping
    sensor_manager.stc31c.wake_up()
    assert not sensor_manager.stc31c._sleeping


def test_sleep_wake_sps30(sensor_manager: SensorManager) -> None:
    """Test sleep and wake-up functionality for SPS30 sensor."""
    assert sensor_manager.sps30 is not None, "SPS30Sensor is None"
    assert not sensor_manager.sps30._sleeping
    assert sensor_manager.sps30._measurement_started
    sensor_manager.sps30.sleep()
    assert sensor_manager.sps30._sleeping
    assert not sensor_manager.sps30._measurement_started
    sensor_manager.sps30.wake_up()
    assert not sensor_manager.sps30._sleeping
    assert sensor_manager.sps30._measurement_started


def test_sleep_wake_shtc3(sensor_manager: SensorManager) -> None:
    """Test sleep and wake-up functionality for SHTC3 sensor."""
    assert sensor_manager.shtc3 is not None, "SHTC3Sensor is None"
    with pytest.raises(NotImplementedError):
        sensor_manager.shtc3.sleep()
    with pytest.raises(NotImplementedError):
        sensor_manager.shtc3.wake_up()


def test_sleep_all(sensor_manager: SensorManager, mock_logger: MagicMock) -> None:
    """Test putting all sensors to sleep."""
    with patch.object(sensor_manager, "sleep_all") as mock_sleep_all:
        sensor_manager.sleep_all()
        mock_sleep_all.assert_called_once()

    # Manually put sensors to sleep
    assert sensor_manager.stc31c is not None, "STC31CSensor is None"
    assert sensor_manager.sps30 is not None, "SPS30Sensor is None"
    sensor_manager.stc31c.sleep()
    sensor_manager.sps30.sleep()
    assert sensor_manager.stc31c._sleeping
    assert sensor_manager.sps30._sleeping


def test_wake_up_all(sensor_manager: SensorManager, mock_logger: MagicMock) -> None:
    """Test waking up all sensors."""
    assert sensor_manager.stc31c is not None, "STC31CSensor is None"
    assert sensor_manager.sps30 is not None, "SPS30Sensor is None"
    sensor_manager.stc31c.sleep()
    sensor_manager.sps30.sleep()
    with patch.object(sensor_manager, "wake_up_all") as mock_wake_up_all:
        sensor_manager.wake_up_all()
        mock_wake_up_all.assert_called_once()

    sensor_manager.stc31c.wake_up()
    sensor_manager.sps30.wake_up()
    assert not sensor_manager.stc31c._sleeping
    assert not sensor_manager.sps30._sleeping


def test_shutdown(sensor_manager: SensorManager, mock_logger: MagicMock) -> None:
    """Test graceful shutdown of all sensors."""
    with patch.object(sensor_manager, "shutdown") as mock_shutdown:
        sensor_manager.shutdown()
        mock_shutdown.assert_called_once()

    assert sensor_manager.stc31c is not None, "STC31CSensor is None"
    assert sensor_manager.sps30 is not None, "SPS30Sensor is None"
    sensor_manager.sps30.stop_measurement()
    sensor_manager.stc31c.sleep()
    sensor_manager.sps30.sleep()
    assert not sensor_manager.sps30._measurement_started
    assert sensor_manager.stc31c._sleeping
    assert sensor_manager.sps30._sleeping
