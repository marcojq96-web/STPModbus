# Sky Toppower STP2S3010E22 Control Center ⚡

A modern desktop application built in Python to monitor and control the **Sky Toppower STP2S3010E22** programmable power supply via Modbus RTU (Serial communication).

## Features
- **Auto-Scan COM Ports:** Detects available serial connections instantly.
- **Live Telemetry:** Background monitoring loop for real-time Voltage and Current displays.
- **Mode Tracking:** Automatically identifies and highlights **CV (Constant Voltage)** and **CC (Constant Current)** modes.
- **Full Control UI:** Easy configuration tools to apply target voltage, current limits, and toggle Over-Current Protection (OCP).
- **Safety Lock:** Gracefully disconnects and stops power output upon window closure.

## Prerequisites
Before running the application, make sure you have:
1. Python 3.8 or higher installed.
2. The power supply connected via USB/Serial cable to your computer.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd YOUR_REPO_NAME
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Simply run the main Python script to launch the interface:
```bash
python main.py
```
*Replace `main.py` with your exact filename if it is different.*

1. Select your power supply's **COM Port** from the dropdown menu (click 🔄 if it doesn't show up immediately).
2. Click **Connect Device**.
3. Set your desired values and click **⚡ OUTPUT ON** to begin.

## Tech Stack
- **GUI Framework:** [CustomTkinter](https://github.com) (Dark mode theme)
- **Protocol Communication:** [PyModbus](https://github.com)
- **Concurrency:** Python standard `threading` library for lag-free UI updates.