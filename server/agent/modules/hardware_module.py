import os
import subprocess
import logging
import psutil
try:
    import pywin32_system32 # This is a hack to check if pywin32 might be available
    import win32print
except ImportError:
    win32print = None

logger = logging.getLogger("AutoOS.hardware_module")

async def handle_hardware_task(task: str) -> str:
    """Handles hardware-related tasks."""
    task_lower = task.lower()
    
    if "printer" in task_lower:
        return await check_printer_status()
    
    if "wifi" in task_lower or "internet" in task_lower or "network" in task_lower:
        return await troubleshoot_network()
    
    if "usb" in task_lower or "pendrive" in task_lower:
        return await check_usb_devices()
        
    if "troubleshoot" in task_lower or "fix" in task_lower:
        return await launch_windows_troubleshooter(task)

    return "I can help you check your printer, Wi-Fi, or USB drives. What would you like me to look at?"

async def check_printer_status() -> str:
    """Checks the status of the default printer."""
    if win32print is None:
        return "I'm sorry, I don't have the necessary tools (pywin32) to check your printer right now."
        
    try:
        printer_name = win32print.GetDefaultPrinter()
        return f"Your default printer is '{printer_name}'. It seems to be connected. If it's not printing, I can try to run the troubleshooter for you."
    except Exception as e:
        return f"I couldn't find a default printer. Please make sure your printer is turned on and plugged in."

async def troubleshoot_network() -> str:
    """Checks internet connection and offers help."""
    try:
        # Ping Google DNS
        subprocess.check_call(["ping", "-n", "1", "8.8.8.8"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Your internet connection seems to be working fine. If you're having trouble with a specific website, I can help you check that."
    except subprocess.CalledProcessError:
        return "It looks like you're not connected to the internet. I recommend checking if your Wi-Fi is turned on or if your cable is plugged in. I can also start the Windows Network Troubleshooter for you."

async def check_usb_devices() -> str:
    """Checks for connected USB storage devices."""
    # This is a simple check using psutil for disk partitions
    usb_drives = []
    for part in psutil.disk_partitions():
        if 'removable' in part.opts or 'cdrom' in part.opts:
            usb_drives.append(part.mountpoint)
            
    if not usb_drives:
        return "I couldn't find any USB drives or pendrives connected to your computer. Try unplugging it and plugging it back in."
    
    return f"I found {len(usb_drives)} connected drive(s): {', '.join(usb_drives)}. You can find them in 'This PC' in your file explorer."

async def launch_windows_troubleshooter(task: str) -> str:
    """Launches specific Windows troubleshooters."""
    task_lower = task.lower()
    
    # Mapping of keywords to troubleshooting IDs
    # List of troubleshooting packs: https://learn.microsoft.com/en-us/windows/deployment/troubleshoot-windows-with-msdt
    troubleshooters = {
        "sound": "AudioPlaybackDiagnostic",
        "audio": "AudioPlaybackDiagnostic",
        "printer": "PrinterDiagnostic",
        "network": "NetworkDiagnosticsWeb",
        "internet": "NetworkDiagnosticsWeb",
        "wifi": "NetworkDiagnosticsWeb",
        "keyboard": "KeyboardDiagnostic",
        "power": "PowerDiagnostic"
    }
    
    for key, pack in troubleshooters.items():
        if key in task_lower:
            try:
                subprocess.Popen(["msdt.exe", "/id", pack])
                return f"I've started the Windows {key.capitalize()} Troubleshooter for you. Please follow the instructions on the screen."
            except Exception as e:
                return f"I tried to start the troubleshooter but something went wrong: {str(e)}"
                
    return "I can start troubleshooters for Sound, Printer, Internet, or Power. Which one do you need?"
