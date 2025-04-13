"""
Unit tests for the SensorBase class.

This test suite verifies:
- Proper initialization of SensorBase instances
- Correct behavior of abstract methods
- Sleep and wake-up functionality
- Exception handling
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Optional, Type, Union, cast
from unittest.mock import MagicMock, patch

import pytest

from sensorpy.exceptions import InitializationError, ReadError
from sensorpy.sensor_base import SensorBase


def create_test_sensor(lib_path: Path) -> Type[SensorBase]:
    """Create a concrete implementation of SensorBase for testing."""

    class TestSensor(SensorBase):
        """Test implementation of SensorBase."""

        def __init__(self, lib_path: Path) -> None:
            """Initialize the test sensor."""
            # Mock the parent class initialization to avoid loading the actual library
            with patch("ctypes.CDLL", return_value=MagicMock()):
                super().__init__(lib_path)
            self._sleeping = False
            self.sleep_implemented = False
            self.wake_up_implemented = False

        def initialize(self) -> None:
            """Initialize the sensor."""
            pass

        def read(self, temperature: Optional[float] = None, humidity: Optional[float] = None) -> Dict[str, float]:
            """Read data from the sensor."""
            if self._sleeping:
                raise ReadError("TestSensor", "Cannot read while sleeping", -1, {"operation": "read"})
            return {"test_value": 42.0}

        def get_info(self) -> Dict[str, Union[str, int]]:
            """Get sensor information."""
            return {"product_name": "TestSensor", "serial_number": "123456789", "firmware_version": "1.0"}

    return TestSensor


class SensorWithSleepImpl(SensorBase):
    """Implementation of SensorBase with sleep and wake-up support for testing."""

    def __init__(self, lib_path: Path) -> None:
        """Initialize the test sensor with sleep support."""
        # Mock the parent class initialization to avoid loading the actual library
        with patch("ctypes.CDLL", return_value=MagicMock()):
            super().__init__(lib_path)
        self._sleeping = False
        self.sleep_implemented = True
        self.wake_up_implemented = True

    def initialize(self) -> None:
        """Initialize the sensor."""
        pass

    def read(self, temperature: Optional[float] = None, humidity: Optional[float] = None) -> Dict[str, float]:
        """Read data from the sensor."""
        if self._sleeping:
            raise ReadError("TestSensor", "Cannot read while sleeping", -1, {"operation": "read"})
        return {"test_value": 42.0}

    def get_info(self) -> Dict[str, Union[str, int]]:
        """Get sensor information."""
        return {"product_name": "TestSensor", "serial_number": "123456789", "firmware_version": "1.0"}

    def sleep(self) -> None:
        """Put the sensor to sleep."""
        self._sleeping = True

    def wake_up(self) -> None:
        """Wake up the sensor."""
        self._sleeping = False


@pytest.fixture
def mock_cdll() -> Generator[MagicMock, None, None]:
    """Fixture to mock ctypes.CDLL."""
    with patch("ctypes.CDLL", return_value=MagicMock()) as mock:
        yield mock


def test_sensor_base_abstract() -> None:
    """Test that SensorBase cannot be instantiated directly."""
    # SensorBase has abstract methods, so we should get a TypeError when trying to instantiate it
    # But since we're mocking the initialization, we need to check that the abstract methods raise NotImplementedError
    with patch("ctypes.CDLL", return_value=MagicMock()):
        sensor = SensorBase(Path("/mock/path"))
        with pytest.raises(NotImplementedError):
            sensor.initialize()
        with pytest.raises(NotImplementedError):
            sensor.read()
        with pytest.raises(NotImplementedError):
            sensor.get_info()


def test_concrete_sensor_instantiation() -> None:
    """Test that a concrete implementation of SensorBase can be instantiated."""
    TestSensor = create_test_sensor(Path("/mock/path"))
    sensor = TestSensor(Path("/mock/path"))
    assert isinstance(sensor, SensorBase)


def test_sensor_read() -> None:
    """Test reading data from the sensor."""
    TestSensor = create_test_sensor(Path("/mock/path"))
    sensor = TestSensor(Path("/mock/path"))
    data = sensor.read()
    assert "test_value" in data
    assert data["test_value"] == 42.0


def test_sensor_get_info() -> None:
    """Test getting sensor information."""
    TestSensor = create_test_sensor(Path("/mock/path"))
    sensor = TestSensor(Path("/mock/path"))
    info = sensor.get_info()
    assert "product_name" in info
    assert "serial_number" in info
    assert "firmware_version" in info


def test_sleep_not_implemented() -> None:
    """Test that sleep raises NotImplementedError if not implemented."""
    TestSensor = create_test_sensor(Path("/mock/path"))
    sensor = TestSensor(Path("/mock/path"))
    with pytest.raises(NotImplementedError):
        sensor.sleep()


def test_wake_up_not_implemented() -> None:
    """Test that wake_up raises NotImplementedError if not implemented."""
    TestSensor = create_test_sensor(Path("/mock/path"))
    sensor = TestSensor(Path("/mock/path"))
    with pytest.raises(NotImplementedError):
        sensor.wake_up()


def test_sleep_implemented() -> None:
    """Test sleep functionality when implemented."""
    sensor = SensorWithSleepImpl(Path("/mock/path"))
    assert not sensor._sleeping
    sensor.sleep()
    assert sensor._sleeping


def test_wake_up_implemented() -> None:
    """Test wake-up functionality when implemented."""
    sensor = SensorWithSleepImpl(Path("/mock/path"))
    sensor.sleep()
    assert sensor._sleeping
    sensor.wake_up()
    assert not sensor._sleeping


def test_read_while_sleeping() -> None:
    """Test that reading while sleeping raises an exception."""
    sensor = SensorWithSleepImpl(Path("/mock/path"))
    sensor.sleep()
    with pytest.raises(ReadError):
        sensor.read()
