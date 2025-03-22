# Fluid Controller

This repository contains software and firmware for a custom fluid control system, featuring PID-based flow rate control, intuitive graphical interfaces, real-time plotting, and reliable hardware communication.

---

## Overview

The project includes two primary components:

- **Controller Interface (GUI)**: A Python-based graphical user interface for real-time monitoring, PID tuning, and easy control of the fluid system.
- **PID Controller (Firmware)**: Arduino-compatible firmware implementing precise PID flow control, valve actuation, sensor reading, and communication logic.

---

## Repository Structure

```
fluid_controller/
├── controller_interface/     # GUI software (Python)
│   ├── build/                # Build files
│   ├── dist/                 # Distributable executables
│   └── src/                  # Source code for GUI
│       ├── controller_interface/
│       │   ├── core/         # Backend logic and communication
│       │   ├── gui/          # Graphical interface elements
│       │   └── resources/    # Icons and images
│       └── test/             # Testing scripts
│
├── pid_controller/           # Arduino firmware (C++)
│   └── _controller/
│       ├── config.h/cpp      # System configurations
│       ├── pid.h/cpp         # PID controller logic
│       ├── flow.h/cpp        # Flow sensor logic
│       ├── sigmoidal_control.h/cpp # Advanced gain scheduling
│       └── _controller.ino   # Main Arduino sketch
│
├── test_hardware/            # Arduino sketches for hardware testing
│
├── flow_volume.json          # Flow volume configuration data
├── pid_controller.zip        # Archive of PID controller code
└── README.md                 # Project documentation
```

---

## Features

### Controller Interface (GUI)

- Real-time data visualization and PID tuning
- User-friendly layout with customizable themes
- Direct serial communication to embedded hardware
- Easy-to-use GUI controls for hardware interaction

### PID Controller Firmware

- Accurate PID control algorithm with dynamic tuning
- Flow rate measurement and regulation
- Adaptive gain control via sigmoidal functions
- Reliable serial communication for GUI integration

---

## Getting Started

### GUI Installation & Usage

**Prerequisites**:

- Python (≥ 3.8)
- Required Python packages (PyQt6/PySide6, numpy, matplotlib)

**Installation**:

```bash
cd controller_interface
pip install -r requirements.txt
```

**Running the GUI**:

```bash
python src/controller_interface/main.py
```

**Building Standalone Executable (Windows)**:

```bash
./build.bat
```

### Firmware Installation & Upload (Arduino)

1. Open the Arduino IDE.
2. Load the sketch `_controller/_controller.ino`.
3. Connect the Arduino board to your computer via USB.
4. Select your Arduino model and COM port.
5. Compile and upload the sketch to the board.

---

## Hardware Testing

Inside the `test_hardware/` folder, you'll find Arduino sketches designed to test:

- I²C communication (`i2c_check`, `test_i2c`)
- Flow sensors (`test_sensor`, `test_sensor_2`)
- Buttons and other inputs (`test_buttons`)

Load these sketches onto your Arduino hardware for troubleshooting and verification purposes.

---

## Dependencies

- Python ≥ 3.8
- PyQt6 / PySide6 (listed in `requirements.txt`)
- numpy, matplotlib (listed in `requirements.txt`)
- Arduino IDE (for firmware)

- Email: [ropeters@valdosta.edu]
