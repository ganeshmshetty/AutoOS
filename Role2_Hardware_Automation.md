# Role 2: Hardware & Peripheral Automation

## Objective
Implement automated troubleshooting and status monitoring for physical devices and hardware using Python 3.12 and Agent-S.

## Tech Stack
- **Python 3.12**
- **Agent-S** (`gui-agents`)
- **System APIs**: `pywin32`, `psutil`, `subprocess`

## Tasks & Requirements

### 1. Automated Troubleshooter
- **Functionality**: Trigger Windows Troubleshooters for Sound, Printer, and Network.
- **Agent-S Integration**: Use Agent-S to visually navigate the "Settings" or "Control Panel" troubleshooters, clicking "Next" and following instructions automatically so the user doesn't have to.

### 2. Peripheral Status Monitoring
- **Functionality**: Check if USB drives, Printers, or Bluetooth devices are connected and working.
- **Reporting**: Report status in plain English (e.g., "Your printer is out of paper" instead of "Error Code 12").

### 3. Networking Diagnostics
- **Functionality**: Check Wi-Fi signal strength and internet connectivity.
- **Automation**: Reset the network adapter or toggle Wi-Fi if a connection is lost.

### 4. Power & Battery Health
- **Functionality**: Monitor battery percentage and charging status.
- **Alerts**: Provide proactive alerts about battery health and estimated remaining time.

## Rules
- **Non-Invasive**: Automation should be smooth and explain what it is doing ("I'm checking your printer now...").
- **Visual Grounding**: Use Agent-S to verify that hardware-related UI dialogs (like "Format Disk") are handled safely.
