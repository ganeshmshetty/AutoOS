"""
hardware_module.py — Hardware detection and troubleshooting for AutoOS.
Uses action_params.device_type from the planner for precise dispatch.
"""
from __future__ import annotations

import asyncio
import logging
import subprocess

logger = logging.getLogger("AutoOS.hardware_module")


async def run(task: str, entities: list[str], action_params: dict) -> str:
    device_type: str = action_params.get("device_type", "").lower()

    # Use structured device_type first, fallback to keyword scan
    if device_type in ("usb", "pendrive", "flash_drive", "storage"):
        return await _check_usb()
    if device_type in ("wifi", "wi-fi", "network", "internet"):
        return await _fix_wifi(task.lower())
    if device_type in ("printer", "print"):
        return await _check_printer()
    if device_type in ("sound", "audio", "speaker", "microphone"):
        return await _run_troubleshooter("audio")
    if device_type in ("bluetooth",):
        return await _check_bluetooth()

    # Fallback keyword scan on raw task
    task_lower = task.lower()
    if any(w in task_lower for w in ("usb", "pendrive", "pen drive", "flash drive")):
        return await _check_usb()
    if any(w in task_lower for w in ("wifi", "wi-fi", "internet", "network")):
        return await _fix_wifi(task_lower)
    if any(w in task_lower for w in ("printer", "print")):
        return await _check_printer()
    if any(w in task_lower for w in ("sound", "audio", "speaker", "mic")):
        return await _run_troubleshooter("audio")
    if "bluetooth" in task_lower:
        return await _check_bluetooth()

    return await _run_troubleshooter("devices")


async def _check_usb() -> str:
    try:
        import psutil
        partitions = psutil.disk_partitions(all=True)
        usb_drives = [
            p for p in partitions
            if "removable" in p.opts.lower() or p.fstype.lower() in ("fat32", "exfat", "fat")
        ]
        if not usb_drives:
            return (
                "No USB drives are connected right now.\n"
                "Please try unplugging and reconnecting the drive firmly, then ask me again."
            )
        lines = [f"Found {len(usb_drives)} USB drive(s) connected:\n"]
        for p in usb_drives:
            try:
                usage = psutil.disk_usage(p.mountpoint)
                gb_free = usage.free / (1024 ** 3)
                gb_total = usage.total / (1024 ** 3)
                lines.append(
                    f"  Drive {p.mountpoint} — {gb_free:.1f} GB free of {gb_total:.1f} GB  ({p.fstype})"
                )
            except Exception:
                lines.append(f"  Drive {p.mountpoint} ({p.fstype})")
        return "\n".join(lines)
    except Exception as exc:
        return f"Could not check USB drives: {exc}"


async def _fix_wifi(task_lower: str) -> str:
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout

        if "disconnected" in output.lower() or not output.strip():
            subprocess.run(["netsh", "winsock", "reset"], capture_output=True, timeout=15)
            subprocess.run(["netsh", "int", "ip", "reset"], capture_output=True, timeout=15)
            subprocess.run(["ipconfig", "/release"], capture_output=True, timeout=10)
            subprocess.run(["ipconfig", "/renew"], capture_output=True, timeout=20)
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, timeout=10)
            return (
                "Your Wi-Fi appeared disconnected so I reset the network settings.\n"
                "Please wait a few seconds and check if your internet is working.\n"
                "You may need to reconnect to your Wi-Fi network."
            )

        ssid_line = next((l for l in output.splitlines() if "SSID" in l and "BSSID" not in l), None)
        signal_line = next((l for l in output.splitlines() if "Signal" in l), None)
        ssid = ssid_line.split(":", 1)[-1].strip() if ssid_line else "Unknown"
        signal = signal_line.split(":", 1)[-1].strip() if signal_line else "Unknown"

        return (
            f"Your Wi-Fi is connected.\n"
            f"  Network: {ssid}\n"
            f"  Signal strength: {signal}\n\n"
            f"If you cannot load websites, try turning your router off and on again."
        )
    except Exception as exc:
        return f"Could not check Wi-Fi status: {exc}"


async def _check_printer() -> str:
    try:
        result = subprocess.run(
            [
                "powershell", "-Command",
                "Get-Printer | Select-Object Name,PrinterStatus | ConvertTo-Json"
            ],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0 or not result.stdout.strip():
            return (
                "No printers found on your computer.\n"
                "Make sure the printer is turned on and connected, then ask me again."
            )
        import json
        printers = json.loads(result.stdout)
        if isinstance(printers, dict):
            printers = [printers]
        lines = [f"Found {len(printers)} printer(s):\n"]
        for p in printers:
            status = p.get("PrinterStatus", "Unknown")
            status_text = "Ready" if status == 3 else f"Status code: {status} (may need attention)"
            lines.append(f"  {p.get('Name', 'Unknown')} — {status_text}")
        return "\n".join(lines)
    except Exception as exc:
        return f"Could not check printers: {exc}"


async def _check_bluetooth() -> str:
    try:
        result = subprocess.run(
            [
                "powershell", "-Command",
                "Get-PnpDevice -Class Bluetooth | Select-Object FriendlyName,Status | ConvertTo-Json"
            ],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0 or not result.stdout.strip():
            return "No Bluetooth devices found. Make sure Bluetooth is turned on."
        import json
        devices = json.loads(result.stdout)
        if isinstance(devices, dict):
            devices = [devices]
        lines = [f"Found {len(devices)} Bluetooth device(s):\n"]
        for d in devices:
            lines.append(f"  {d.get('FriendlyName', 'Unknown')} — {d.get('Status', 'Unknown')}")
        return "\n".join(lines)
    except Exception as exc:
        return f"Could not check Bluetooth: {exc}"


async def _run_troubleshooter(category: str) -> str:
    troubleshooter_ids = {
        "audio":    "msdt.exe -id AudioPlaybackDiagnostic",
        "internet": "msdt.exe -id NetworkDiagnosticsWeb",
        "printer":  "msdt.exe -id PrinterDiagnostic",
        "devices":  "msdt.exe -id DeviceDiagnostic",
    }
    cmd = troubleshooter_ids.get(category, "msdt.exe -id DeviceDiagnostic")
    try:
        subprocess.Popen(cmd, shell=True)
        return (
            f"I opened the Windows {category} troubleshooter for you.\n"
            f"Please follow the on-screen steps — it will try to fix the problem automatically."
        )
    except Exception as exc:
        return f"Could not open the troubleshooter: {exc}"
