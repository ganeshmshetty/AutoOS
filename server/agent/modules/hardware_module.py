"""
hardware_module.py — Hardware detection and troubleshooting for AutoOS.
Uses action_params.device_type from the planner for precise dispatch.
"""
from __future__ import annotations
import os
import asyncio
import logging
import subprocess
import ctypes
from ctypes import wintypes
try:
    import win32com.client
    import pythoncom
except ImportError:
    win32com = None
    pythoncom = None

logger = logging.getLogger("AutoOS.hardware_module")

class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ('ACLineStatus', wintypes.BYTE),
        ('BatteryFlag', wintypes.BYTE),
        ('BatteryLifePercent', wintypes.BYTE),
        ('SystemStatusFlag', wintypes.BYTE),
        ('BatteryLifeTime', wintypes.DWORD),
        ('BatteryFullLifeTime', wintypes.DWORD),
    ]


async def run(task: str, entities: list[str], action_params: dict) -> str:
    device_type: str = action_params.get("device_type", "").lower()

    # Special case for combined Wifi and Bluetooth request
    if any(w in task.lower() for w in ("wifi", "wi-fi")) and "bluetooth" in task.lower():
        try:
            os.startfile("ms-settings:network-wifi")
            os.startfile("ms-settings:bluetooth")
        except:
            pass
        wifi_task = asyncio.create_task(_get_available_wifi_networks())
        bt_task = asyncio.create_task(_check_bluetooth())
        wifi_res = await wifi_task
        bt_res = await bt_task
        return f"I have opened both your Wi-Fi and Bluetooth settings.\n\n{wifi_res}\n\n{bt_res}"

    if device_type in ("usb", "pendrive", "flash_drive", "storage"):
        return await _check_usb()
    if device_type in ("wifi", "wi-fi", "network", "internet"):
        if any(w in task.lower() for w in ("available", "nearby", "list", "scan", "show", "same")):
            return await _get_available_wifi_networks()
        if any(w in task.lower() for w in ("toggle", "turn", "on", "off", "switch", "open", "settings")):
            return await _open_wifi_settings()
        return await _fix_wifi(task.lower())
    if device_type in ("printer", "print"):
        return await _check_printer()
    if device_type in ("sound", "audio", "speaker", "microphone", "volume"):
        if any(w in task.lower() for w in ("up", "down", "increase", "decrease", "higher", "lower", "mute", "unmute", "set")):
            return await _control_volume(task.lower())
        return await _run_troubleshooter("audio")
    if device_type in ("bluetooth",):
        if "toggle" in task.lower() or "turn" in task.lower() or "switch" in task.lower():
            return await _open_bluetooth_settings()
        return await _check_bluetooth()
    if device_type in ("battery", "power", "charge"):
        return await _get_battery_info()

    # Fallback keyword scan on raw task
    task_lower = task.lower()
    if any(w in task_lower for w in ("usb", "pendrive", "pen drive", "flash drive")):
        return await _check_usb()
    if any(w in task_lower for w in ("wifi", "wi-fi", "internet", "network")):
        if any(w in task_lower for w in ("available", "nearby", "list", "scan", "show", "same")):
            return await _get_available_wifi_networks()
        if any(w in task_lower for w in ("toggle", "turn", "on", "off", "switch", "open", "settings")):
            return await _open_wifi_settings()
        return await _fix_wifi(task_lower)
    if any(w in task_lower for w in ("printer", "print")):
        return await _check_printer()
    if any(w in task_lower for w in ("sound", "audio", "speaker", "mic")):
        return await _run_troubleshooter("audio")
    if "bluetooth" in task_lower:
        if any(w in task_lower for w in ("toggle", "turn", "on", "off", "switch")):
            return await _open_bluetooth_settings()
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
        
        # Open storage settings for the user
        os.startfile("ms-settings:storagesense")

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
        
        lines.append("\nI have also opened your Storage settings for you.")
        return "\n".join(lines)
    except Exception as exc:
        return f"Could not check USB drives: {exc}"


async def _get_battery_info() -> str:
    status = SYSTEM_POWER_STATUS()
    if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        percent = status.BatteryLifePercent
        ac = "plugged in" if status.ACLineStatus == 1 else "on battery power"
        if percent == 255:
            return "I couldn't detect a battery. Are you on a desktop computer?"
        
        msg = f"Your battery is at {percent}% and is currently {ac}."
        if status.ACLineStatus == 0 and status.BatteryLifeTime != 0xFFFFFFFF:
            hours = status.BatteryLifeTime // 3600
            mins = (status.BatteryLifeTime % 3600) // 60
            msg += f"\nEstimated time remaining: {hours}h {mins}m"
        return msg
    return "I couldn't retrieve the battery status via Windows API."


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
    """Query printers in a background thread."""
    if not win32com: return "WMI not available."
    return await asyncio.to_thread(_check_printer_sync)


def _check_printer_sync() -> str:
    """Synchronous WMI printer query."""
    try:
        pythoncom.CoInitialize()
        wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator").ConnectServer(".", r"root\cimv2")
        printers = wmi.ExecQuery("SELECT Name, PrinterStatus FROM Win32_Printer")
        
        if not printers:
            return "No printers found on your computer."
            
        lines = [f"Found {len(printers)} printer(s):\n"]
        for p in printers:
            status = p.PrinterStatus
            status_text = "Ready" if status == 3 else f"Status: {status} (requires attention)"
            lines.append(f"  {p.Name} — {status_text}")
        return "\n".join(lines)
    except Exception as exc:
        logger.error("WMI Printer check failed: %s", exc)
        return f"Could not check printers: {exc}"
    finally:
        pythoncom.CoUninitialize()


async def _check_bluetooth() -> str:
    """Query Bluetooth devices and open settings."""
    if not win32com: return "WMI not available."
    try:
        os.startfile("ms-settings:bluetooth")
    except:
        pass
    return await asyncio.to_thread(_check_bluetooth_sync)


def _check_bluetooth_sync() -> str:
    """Synchronous WMI Bluetooth query."""
    try:
        pythoncom.CoInitialize()
        wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator").ConnectServer(".", r"root\cimv2")
        # Use the standard Bluetooth Class GUID for the most reliable discovery
        devices = wmi.ExecQuery("SELECT Name, Status FROM Win32_PnPEntity WHERE ClassGuid = '{e0cbf06c-cd8b-4647-bb8a-263b43f0f974}'")
        
        if not devices:
            return "No Bluetooth devices found. Make sure Bluetooth is turned on."
            
        lines = [f"Found {len(devices)} Bluetooth device(s):\n"]
        for d in devices:
            lines.append(f"  {d.Name} — {d.Status}")
        
        return "\n".join(lines)
    except Exception as exc:
        logger.error("WMI Bluetooth check failed: %s", exc)
        return f"Could not check Bluetooth: {exc}"
    finally:
        pythoncom.CoUninitialize()


async def _get_available_wifi_networks() -> str:
    try:
        # Open settings first for the user
        os.startfile("ms-settings:network-wifi")
        
        # Scan for networks
        result = subprocess.run(
            ["netsh", "wlan", "show", "networks"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        
        networks = []
        for line in output.splitlines():
            if "SSID" in line and ":" in line:
                ssid = line.split(":", 1)[1].strip()
                if ssid:
                    networks.append(ssid)
        
        if not networks:
            return (
                "I couldn't find any available Wi-Fi networks in range.\n"
                "I have opened your Wi-Fi settings so you can check if your Wi-Fi adapter is turned on."
            )
        
        msg = "I found the following Wi-Fi networks nearby:\n\n"
        msg += "\n".join([f"• {n}" for n in networks])
        msg += "\n\nI have also opened your Wi-Fi settings for you to connect."
        return msg
    except Exception as exc:
        os.startfile("ms-settings:network-wifi")
        return f"I opened your Wi-Fi settings, but I had trouble listing the networks via text: {exc}"


async def _open_wifi_settings() -> str:
    os.startfile("ms-settings:network-wifi")
    return "I opened the Wi-Fi settings for you. You can turn Wi-Fi on or off using the switch there."


async def _open_bluetooth_settings() -> str:
    os.startfile("ms-settings:bluetooth")
    return "I opened the Bluetooth settings for you. You can turn Bluetooth on or off there."


async def _control_volume(task_lower: str) -> str:
    """Instant volume control using Windows Message API."""
    try:
        # APPCOMMAND_VOLUME_MUTE = 0x80000 (8 << 16)
        # APPCOMMAND_VOLUME_DOWN = 0x90000 (9 << 16)
        # APPCOMMAND_VOLUME_UP   = 0xA0000 (10 << 16)
        
        WM_APPCOMMAND = 0x0319
        CMD_MUTE = 8 << 16
        CMD_DOWN = 9 << 16
        CMD_UP   = 10 << 16
        
        # Get handle to any window to send the message to (the system will catch it)
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        
        if "mute" in task_lower or "unmute" in task_lower:
            ctypes.windll.user32.SendMessageW(hwnd, WM_APPCOMMAND, 0, CMD_MUTE)
            return "Volume muted/unmuted."
        
        if any(w in task_lower for w in ("up", "increase", "higher", "more")):
            # Send multiple times for noticeable effect
            for _ in range(5):
                ctypes.windll.user32.SendMessageW(hwnd, WM_APPCOMMAND, 0, CMD_UP)
            return "Volume increased."
        
        if any(w in task_lower for w in ("down", "decrease", "lower", "less")):
            for _ in range(5):
                ctypes.windll.user32.SendMessageW(hwnd, WM_APPCOMMAND, 0, CMD_DOWN)
            return "Volume decreased."
            
        return "I can increase, decrease, or mute your volume. What would you like me to do?"
    except Exception as exc:
        return f"Could not control volume: {exc}"


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
