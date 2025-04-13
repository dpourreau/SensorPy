"""
This example demonstrates how to initialize and read data from actual Sensirion sensors:
- STC31C CO2 sensor
- SHTC3 temperature and humidity sensor
- SPS30 particulate matter sensor

Requirements:
- Sensirion sensors physically connected to your device
- Appropriate permissions to access I2C and UART interfaces
- Sensor driver libraries compiled and available
"""

import logging
import sys
import time
from pathlib import Path

# Add the parent directory to the path so we can import the sensorpy module
sys.path.insert(0, str(Path(__file__).parent.parent))

from sensorpy import setup_logging

# Import the real sensor manager
from sensorpy.sensor_manager import SensorManager


def main() -> None:
    """
    Main function to initialize real sensors, retrieve sensor metadata, and continuously
    read sensor measurements.
    """
    # Setup logging to see informational messages
    setup_logging(level=logging.INFO)

    # Path to the sensor driver libraries
    # Corrected path - libraries are in SensorPy/drivers_c/build, not in the parent directory
    lib_path = Path(__file__).resolve().parent.parent / "drivers_c" / "build"

    print(f"Looking for sensor drivers at: {lib_path}")
    print("Initializing real sensors. Make sure they are properly connected...")

    try:
        # Initialize the real sensor manager, which sets up all sensors
        sensor_manager = SensorManager(lib_path=lib_path)

        # Retrieve and display sensor metadata (serial numbers, firmware versions, etc.)
        sensor_info = sensor_manager.get_all_info()

        print("\nSensor Information:")
        print("-" * 50)
        if "stc31c" in sensor_info:
            print("\nSTC31-C Information:")
            print(f"Product Name: {sensor_info['stc31c'].get('product_name', 'N/A')}")
            print(f"Serial Number: {sensor_info['stc31c'].get('serial_number', 'N/A')}")
            print(f"Firmware Version: {sensor_info['stc31c'].get('firmware_version', 'N/A')}")
        if "shtc3" in sensor_info:
            print("\nSHTC3 Information:")
            print(f"Product Name: {sensor_info['shtc3'].get('product_name', 'N/A')}")
            print(f"Serial Number: {sensor_info['shtc3'].get('serial_number', 'N/A')}")
            print(f"Firmware Version: {sensor_info['shtc3'].get('firmware_version', 'N/A')}")
        if "sps30" in sensor_info:
            print("\nSPS30 Information:")
            print(f"Product Name: {sensor_info['sps30'].get('product_name', 'N/A')}")
            print(f"Serial Number: {sensor_info['sps30'].get('serial_number', 'N/A')}")
            print(f"Firmware Version: {sensor_info['sps30'].get('firmware_version', 'N/A')}")

        print("\nStarting continuous measurement...")
        print("-" * 50)

        # Continuous measurement loop
        while True:
            assert sensor_manager.shtc3 is not None, "SHTC3 sensor not available"
            shtc3_data = sensor_manager.shtc3.read()
            temperature = shtc3_data.get("temperature")
            humidity = shtc3_data.get("relative_humidity")

            assert sensor_manager.stc31c is not None, "STC31C sensor not available"
            stc31c_data = sensor_manager.stc31c.read(temperature=temperature, humidity=humidity)

            assert sensor_manager.sps30 is not None, "SPS30 sensor not available"
            sps30_data = sensor_manager.sps30.read()

            print("\nCurrent Readings:")
            print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("\nEnvironmental Conditions:")
            print(f"Temperature: {temperature:.1f} °C")
            print(f"Humidity: {humidity:.1f} %RH")
            print("\nGas Concentrations:")
            print(f"CO2: {stc31c_data.get('co2_concentration', 'N/A'):.1f} ppm")
            print("\nParticulate Matter:")
            print("Mass Concentrations:")
            print(f"PM1.0: {sps30_data.get('pm1.0', 'N/A'):.1f} µg/m³")
            print(f"PM2.5: {sps30_data.get('pm2.5', 'N/A'):.1f} µg/m³")
            print(f"PM4.0: {sps30_data.get('pm4.0', 'N/A'):.1f} µg/m³")
            print(f"PM10: {sps30_data.get('pm10.0', 'N/A'):.1f} µg/m³")
            print("\nNumber Concentrations:")
            print(f"NC0.5: {sps30_data.get('nc0.5', 'N/A'):.1f} #/cm³")
            print(f"NC1.0: {sps30_data.get('nc1.0', 'N/A'):.1f} #/cm³")
            print(f"NC2.5: {sps30_data.get('nc2.5', 'N/A'):.1f} #/cm³")
            print(f"NC4.0: {sps30_data.get('nc4.0', 'N/A'):.1f} #/cm³")
            print(f"NC10.0: {sps30_data.get('nc10.0', 'N/A'):.1f} #/cm³")
            print(f"\nTypical Particle Size: {sps30_data.get('typical_particle_size', 'N/A'):.2f} µm")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nMeasurement stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure all sensors are properly connected and the driver libraries are available.")
        sys.exit(1)
    finally:
        print("\nShutting down sensors...")
        sensor_manager.shutdown()


if __name__ == "__main__":
    main()
