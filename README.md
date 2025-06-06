# Fluid Controller
# WIP

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
│  README.md
│  pid_controller.zip
│
├─ controller_interface/           # PyQt GUI application
│  │  build.bat
│  │  Controller_Interface.spec
│  │  LICENSE
│  │  pyproject.toml
│  │  requirements.txt
│  ├─ build/ …                     # (auto-generated by PyInstaller)
│  ├─ dist/  …                     # frozen executables
│  ├─ src/
│  │  ├─ controller_interface/
│  │  │  ├─ controller/            # high-level UI controller classes
│  │  │  ├─ model/                 # data & serial back-end
│  │  │  ├─ view/                  # views, panels, widgets, themes, plots
│  │  │  ├─ resources/             # .qrc + compiled resources_rc.py
│  │  │  └─ utils/                 # logging & path helpers
│  │  └─ test/                     # GUI unit/integration tests
│  └─ README.md                    # GUI-specific notes
│
├─ curve_tools/                    # ad-hoc analysis / plotting scripts
│  ├─ exp_curve_validation.py
│  └─ plotter.py
│
├─ misc_utils/                     # one-off utilities / images
│  ├─ DOT.py
│  └─ run_tree.png
│
├─ pid_controller/                 # Embedded firmware (Arduino / C++)
│  └─ _controller/
│     ├─ _controller.ino           # entry-point sketch
│     ├─ config.*                  # system-wide constants
│     ├─ pid.*                     # core PID engine
│     ├─ exp_control.*             # exponential gain scheduling
│     ├─ sigmoidal_control.*       # (optional) sigmoidal gain scheduling
│     ├─ constant_voltage_control.*# open-loop calibration mode
│     ├─ filter.*                  # adaptive + EMA filters
│     ├─ flow.*                    # I²C flow-sensor driver
│     ├─ bartels.*                 # pump DAC driver
│     ├─ display.*, buttons.*      # OLED + input HW
│     ├─ report.*                  # CSV / JSON telemetry
│     └─ system_state.h            # shared data struct
│
├─ test_hardware/                  # standalone sketches for bench tests
│  ├─ i2c_check/…
│  ├─ test_buttons/…
│  ├─ test_i2c/…
│  └─ test_sensor/…                # sensor sanity checks
└─ flow_volume.json                # per-concentration flow-volume map

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
