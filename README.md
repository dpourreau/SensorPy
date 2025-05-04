# Sensirion Sensors Python Bindings

This package provides Python bindings for Sensirion sensors (**STC31-C**, **SHTC3**, and **SPS30**). It enables easy integration of these sensors into Python applications, allowing you to read measurements through a simple interface.

## Supported Sensors

- **STC31-C**: CO₂ concentration and temperature sensor  
- **SHTC3**: Temperature and humidity sensor  
- **SPS30**: Particulate matter sensor  

## Requirements

- **Python 3.8+**
- **GCC** (for compiling C drivers)
- **Make** (for building the drivers)
- **Linux system** with I²C and UART support
- **Git** (for cloning and managing submodules)

## Project Structure

```
SensorPy/
├── drivers_c/
│   ├── include/                     # Header files
│   │   ├── sensirion_arch_config.h  # Architecture configuration
│   │   ├── sensirion_common.h       # Common utilities
│   │   ├── sensirion_config.h       # Sensor configuration
│   │   ├── sensirion_i2c.h          # I2C protocol
│   │   ├── sensirion_i2c_hal.h      # I2C hardware abstraction
│   │   ├── sensirion_shdlc.h        # SHDLC protocol for UART
│   │   ├── sensirion_uart.h         # UART interface
│   │   ├── sht4x_i2c.h              # SHT4X sensor interface
│   │   ├── sps30.h                  # SPS30 sensor interface
│   │   ├── sps_git_version.h        # Version information
│   │   └── stc3x_i2c.h              # STC3X sensor interface
│   ├── src/                         # Sensor drivers source code
│   │   ├── sps30/                   # SPS30 implementation & example
│   │   │   ├── sps30.c
│   │   │   ├── sensirion_shdlc.c
│   │   │   ├── sensirion_uart_implementation.c
│   │   │   ├── sps30_example_usage.c
│   │   │   └── sps_git_version.c
│   │   └── stc3x/                   # STC3X (and SHT4X) implementation & example
│   │       ├── stc3x_i2c.c
│   │       ├── sensirion_i2c.c
│   │       ├── sensirion_i2c_hal.c
│   │       ├── sensirion_common.c
│   │       ├── sht4x_i2c.c
│   │       └── stc3x_i2c_measurement_with_compensation.c
│   └── Makefile                     # Build system for sensor drivers
├── sensorpy/                        # Python bindings package
│   ├── __init__.py                  # Package initialization
│   ├── exceptions.py                # Custom exceptions for error handling
│   ├── sensor_base.py               # Base class for all sensors
│   ├── structures.py                # C structure definitions
│   ├── sensor_manager.py            # Manager for coordinating all sensors
│   ├── sps30_sensor.py              # SPS30 particulate matter sensor implementation
│   ├── stc31c_sensor.py             # STC31-C CO₂ sensor implementation
│   ├── shtc3_sensor.py              # SHTC3 temperature and humidity sensor implementation
│   └── py.typed                     # Marker file for type checking
├── examples/
│   └── basic_usage.py               # Basic example for using the sensors via Python
├── tests/                           # Unit tests
│   ├── conftest.py                  # Pytest configuration
│   ├── test_logging.py              # Tests for logging functionality
│   ├── test_sensor_base.py          # Tests for the sensor base class
│   └── test_sensor_manager.py       # Tests for the sensor manager
├── docs/                            # Documentation files
│   ├── DEVELOPER_GUIDELINES.md      # Developer guidelines and best practices
│   └── SENSOR_CONNECTION_GUIDE.md   # Guide for connecting sensors to Raspberry Pi
├── .coveragerc                      # Coverage configuration for pytest
├── pyproject.toml                   # Build and tool configuration
└── setup.py                         # Package setup script
```

## Installation

### 1. Clone the Repository

Because this project uses Git submodules, clone it with:

```bash
# Clone with submodules in one command
git clone --recursive git@github.com:dpourreau/SensorPy.git
cd SensorPy
```

If you already cloned without the `--recursive` flag, initialize submodules manually:

```bash
git submodule update --init --recursive
```

### 2. Build the Sensor Drivers

Compile the sensor drivers as a shared library:

```bash
cd drivers_c
make clean && make
cd ..
```

This command creates a shared library in `drivers_c/build` named `libsensirion.so` and two example executables:
- `drivers_c/build/sps30_example`
- `drivers_c/build/stc3x_example`

*Note:* If you encounter a shared library loading error when running a C example, ensure that your Makefile embeds an absolute rpath.

### 3. Set Up Python Environment

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
```

### 4. Install the Package

Install the package in “editable” (development) mode along with any dev dependencies:

```bash
pip install -e ".[dev]"
```

## Running the Examples

### Python Example

To run the basic Python example:

1. **Activate your virtual environment:**

   ```bash
   source venv/bin/activate
   ```

2. **Run the example:**

   ```bash
   python3 examples/basic_usage.py
   ```

This script initializes the sensors using the shared library built from the sensor drivers and prints sensor information and measurements.

### C Examples

After building the sensor drivers, you can run the C examples:

- **SPS30 Example:**  
  ```bash
  ./drivers_c/build/sps30_example
  ```
- **STC3X Example:**  
  ```bash
  ./drivers_c/build/stc3x_example
  ```

## Documentation

For detailed information on using and contributing to SensorPy, please refer to the documentation files in the `docs/` directory:

- **[Developer Guidelines](docs/DEVELOPER_GUIDELINES.md):**  
  Best practices and guidelines for contributing to the codebase.

- **[Sensor Connection Guide](docs/SENSOR_CONNECTION_GUIDE.md):**  
  Instructions for connecting Sensirion sensors (STC31-C, SHTC3, SPS30) to your Raspberry Pi.

## Contributing

We welcome contributions! If you wish to contribute to SensorPy, please follow these guidelines:

1. **Review the [Developer Guidelines](docs/DEVELOPER_GUIDELINES.md)** to understand our coding standards and development workflow.
2. **Fork the repository** and create a new branch for your feature or bug fix.
3. **Ensure that all tests pass** and that your changes adhere to our style guidelines.
4. **Submit a pull request** with a clear description of your changes.

For further details, please see our contributing documentation in [Developer Guidelines](docs/DEVELOPER_GUIDELINES.md).

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for the full text.

### Third-Party Code

This repository includes C driver code from Sensirion AG, located in the `drivers_c/` directory. These drivers are licensed under the **BSD 3-Clause License**.

The included sensor drivers are adapted from the following official Sensirion repositories:

- [Sensirion/embedded-uart-sps](https://github.com/Sensirion/embedded-uart-sps)
- [Sensirion/raspberry-pi-i2c-stc3x](https://github.com/Sensirion/raspberry-pi-i2c-stc3x)

See [`drivers_c/LICENSE`](https://github.com/dpourreau/pm-gas-sensor-drivers/LICENSE) for the full BSD 3-Clause License text.
