import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger("AutoOS.maintenance_module")

async def handle_maintenance_task(task: str) -> str:
    """Handles storage cleanup and system maintenance."""
    task_lower = task.lower()
    
    if "cleanup" in task_lower or "clean" in task_lower or "storage" in task_lower:
        return await storage_cleanup()
    
    return "I can help you clean up temporary files to save space. Would you like me to do that?"

async def storage_cleanup() -> str:
    """Cleans up temp directories."""
    temp_dirs = [
        os.environ.get('TEMP'),
        os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp')
    ]
    
    cleaned_size = 0
    errors = 0
    
    for d in temp_dirs:
        if not d or not os.path.exists(d):
            continue
        for root, dirs, files in os.walk(d):
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    cleaned_size += os.path.getsize(fp)
                    os.remove(fp)
                except Exception:
                    errors += 1
                    
    size_mb = cleaned_size / (1024 * 1024)
    return f"I've cleaned up approximately {size_mb:.2f} MB of temporary files. Some files were in use and couldn't be deleted, but your system should feel a bit lighter now!"
