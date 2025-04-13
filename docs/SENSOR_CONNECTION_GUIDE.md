# Sensor Connection Guide

This guide explains how to connect the Sensirion sensors to a Raspberry Pi and get them running. It covers the STC31-C (with SHTC3) and the SPS30 sensor. Follow these instructions carefully to ensure proper wiring and configuration.

---

## Connecting Sensirion SEK-STC31-C (with SHTC3) to Raspberry Pi via I²C

### Overview
This guide details how to connect the SEK-STC31-C evaluation kit (which includes both the STC31-C and SHTC3 on a flex PCB) directly to a Raspberry Pi over I²C. This method uses a spliced or adapted RJ45 cable to access the sensor signals.

### Prerequisites
- **Hardware:**
  - Raspberry Pi (any model with a 40-pin header, e.g., Raspberry Pi 4)
  - RJ45 adapter cable that came with the Sensirion kit (cut/spliced as needed)
  - Multimeter (for verifying continuity)
- **Software:**
  - Raspbian OS with I²C enabled

### Pin Mapping and Identification
On the SEK-STC31-C flex PCB, four signals need to be routed:
1. **VDD**
2. **GND**
3. **SCL (I²C Clock)**
4. **SDA (I²C Data)**

#### Steps:
1. **Power Off:** Ensure the Raspberry Pi and sensor are powered off.
2. **Test Continuity:**
   - Set your multimeter to continuity mode.
   - Identify the sensor pads labeled VDD, GND, SCL, and SDA.
   - For each pad, use the multimeter to test each of the four wires from the cut RJ45 cable.
   - Label each wire according to the corresponding sensor pad.
  
### Wiring to the Raspberry Pi
- **VDD:** Connect to Raspberry Pi 3.3V (physical pin 1) or 5V (pins 2 or 4) if the sensor supports 5V.
- **GND:** Connect to any Raspberry Pi GND (e.g., physical pin 6).
- **SCL:** Connect to the Raspberry Pi I²C clock (GPIO 3, physical pin 5).
- **SDA:** Connect to the Raspberry Pi I²C data (GPIO 2, physical pin 3).

### Verifying the Connection
1. **Enable I²C on the Pi:**
   ```bash
   sudo raspi-config
   ```
   Navigate to **Interface Options → I²C → Enable** and reboot if prompted.

2. **Run I²C Detect:**
   ```bash
   sudo i2cdetect -y 1
   ```
   You should see:
   - **0x29** for the STC31-C sensor.
   - **0x44** for the SHTC3 sensor.

---

## Connecting SPS30 via UART to Raspberry Pi

### Overview
This guide details the steps to connect the Sensirion SPS30 sensor to a Raspberry Pi using a UART interface.

### Required Components
- Raspberry Pi (preferably model 3 or 4)
- Sensirion SPS30 Sensor
- Jumper wires

### Pin Connections
Connect the SPS30 sensor to the Raspberry Pi as follows:

| **SPS30 Pin** | **Function**       | **Raspberry Pi Pin**         |
|---------------|--------------------|------------------------------|
| 1 (VDD)       | Power (5V)         | Pin 2 (5V)                   |
| 2 (RX)        | Receive Data (RX)  | Pin 8 (TX - GPIO14)          |
| 3 (TX)        | Transmit Data (TX) | Pin 10 (RX - GPIO15)         |
| 4 (SEL)       | Interface Select   | Leave Floating               |
| 5 (GND)       | Ground             | Pin 9 (GND)                  |

**Important:**  
Ensure that the sensor’s TX is connected to the Raspberry Pi’s RX and vice versa.

### Raspberry Pi Configuration for UART
1. **Configure Serial Port:**
   ```bash
   sudo raspi-config
   ```
   Navigate to **Interface Options → Serial Port** and:
   - **Disable** the login shell over serial.
   - **Enable** the serial port hardware.
2. **Reboot:**
   ```bash
   sudo reboot
   ```
3. **Verify UART:**
   Check the UART symlink:
   ```bash
   ls -l /dev/serial0
   ```
   You should see output similar to:
   ```
   lrwxrwxrwx 1 root root 5 Feb 22 10:23 /dev/serial0 -> ttyS0
   ```

---

## Best Practices for Sensor Setup and Troubleshooting

- **Double-Check Wiring:**  
  Use a multimeter to verify continuity before powering on the system.

- **I²C and UART Tools:**  
  Use `i2cdetect` for I²C and verify UART with `ls -l /dev/serial0`.

- **Documentation:**  
  Refer to this guide and your sensor datasheets for pinouts and specifications.

- **Safe Handling:**  
  Always power off the Raspberry Pi before connecting or disconnecting sensors to avoid damage.

- **Troubleshooting:**  
  - If a sensor does not appear on `i2cdetect` or the UART is not recognized, recheck wiring and ensure that the sensor’s power requirements match the Raspberry Pi’s output.
  - Check dmesg and system logs for error messages related to sensor initialization.

---

## Additional Resources

- [Raspberry Pi GPIO Pinout](https://pinout.xyz/)

---

By following this guide, you should be able to set up your Sensirion sensors with your Raspberry Pi successfully.