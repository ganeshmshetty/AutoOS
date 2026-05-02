import subprocess
import logging

logger = logging.getLogger("AutoOS.security_module")

async def handle_security_task(task: str) -> str:
    """Handles virus scans and windows updates."""
    task_lower = task.lower()
    
    if "scan" in task_lower or "virus" in task_lower:
        return await run_virus_scan()
    
    if "update" in task_lower:
        return await check_windows_updates()
        
    return "I can help you check for updates or run a virus scan. Which would you like?"

async def run_virus_scan() -> str:
    """Triggers a quick scan using Windows Defender CLI."""
    try:
        # MpCmdRun.exe is the Windows Defender command line tool
        # -ScanType 1 is a quick scan
        cmd = r'"C:\Program Files\Windows Defender\MpCmdRun.exe" -Scan -ScanType 1'
        subprocess.Popen(cmd, shell=True)
        return "I've started a quick virus scan with Windows Defender. You can continue using your computer while it runs in the background."
    except Exception as e:
        return f"I tried to start a scan but something went wrong: {str(e)}"

async def check_windows_updates() -> str:
    """Checks for Windows Updates using USOClient."""
    try:
        # USOClient is the modern Windows Update client
        # StartScan starts a check for updates
        subprocess.Popen("usoclient StartScan", shell=True)
        return "I've asked Windows to check for any available updates. If it finds any, you'll see a notification in your system tray."
    except Exception as e:
        return f"I couldn't trigger the update check: {str(e)}"
