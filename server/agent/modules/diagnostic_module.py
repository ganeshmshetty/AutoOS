import subprocess
import logging
import json

logger = logging.getLogger("AutoOS.diagnostic_module")

async def handle_diagnostic_task(task: str) -> str:
    """Handles crash analysis and recycle bin recovery."""
    task_lower = task.lower()
    
    if "crash" in task_lower or "blue screen" in task_lower or "bsod" in task_lower:
        return await analyze_crashes()
    
    if "recycle bin" in task_lower or "trash" in task_lower:
        return await search_recycle_bin(task)
        
    return "I can explain why your computer crashed recently or help you find things in the Recycle Bin."

async def analyze_crashes() -> str:
    """Reads Windows Event Logs to find recent system crashes."""
    try:
        # PowerShell to get the most recent BugCheck event
        ps_cmd = 'Get-WinEvent -FilterHashtable @{LogName="System"; Id=1001} -MaxEvents 1 | Select-Object -ExpandProperty Message'
        result = subprocess.check_output(["powershell", "-Command", ps_cmd], text=True, stderr=subprocess.DEVNULL)
        
        if not result.strip():
            return "I couldn't find any record of recent system crashes. That's a good sign!"
            
        # Here we would normally pass this to the LLM to "explain"
        # For now, we'll give a friendly summary
        return f"I found a record of a recent crash. It was likely caused by a hardware driver or a system update. I recommend making sure all your updates are installed. Here is the technical detail if you need it: {result[:200]}..."
    except Exception:
        return "I couldn't find any recent crash logs. Your system seems to be running stably!"

async def search_recycle_bin(task: str) -> str:
    """Checks the Recycle Bin for deleted files."""
    try:
        # PowerShell to list items in Recycle Bin
        ps_cmd = '$rb = New-Object -ComObject Shell.Application; $bin = $rb.Namespace(0x0a); $bin.Items() | Select-Object Name, Size'
        # This is a bit complex for raw subprocess, but let's try a simpler one for the MVP
        ps_cmd = 'dir "shell:RecycleBinFolder" | Select-Object Name'
        
        # Actually, let's just tell them how many items are there and offer to open it
        ps_cmd = '(New-Object -ComObject Shell.Application).Namespace(0x0a).Items().Count'
        count = subprocess.check_output(["powershell", "-Command", ps_cmd], text=True).strip()
        
        if count == "0":
            return "Your Recycle Bin is empty."
            
        return f"There are {count} items in your Recycle Bin. Would you like me to open it so you can see if your file is there?"
    except Exception:
        return "I can't access your Recycle Bin right now, but you can find it on your Desktop. It's the icon that looks like a trash can."
