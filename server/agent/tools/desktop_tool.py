import os
import asyncio
import pyautogui
import logging
from typing import Optional
from server.agent.modules.file_module import handle_file_task
from server.agent.modules.hardware_module import handle_hardware_task
from server.agent.modules.settings_module import handle_settings_task
from server.agent.modules.security_module import handle_security_task
from server.agent.modules.process_module import handle_process_task
from server.agent.modules.health_module import handle_health_task
from server.agent.modules.diagnostic_module import handle_diagnostic_task
from server.agent.modules.maintenance_module import handle_maintenance_task
from server.agent.modules.browser_helper import handle_browser_help_task
from server.agent.modules.tutorial_module import handle_tutorial_task

logger = logging.getLogger("AutoOS.desktop")

async def run_os_task(task: str, mode: str = "auto") -> str:
    """
    Executes a desktop automation task.
    Routes to specific modules based on task intent.
    """
    logger.info(f"Executing OS task: {task}")
    task_lower = task.lower()

    # Routing logic
    # 1. File tasks
    if any(k in task_lower for k in ["file", "folder", "search", "find", "document", "download", "recycle bin", "trash"]):
        if "recycle bin" in task_lower or "trash" in task_lower:
             return await handle_diagnostic_task(task)
        return await handle_file_task(task)
    
    # 2. Hardware tasks
    if any(k in task_lower for k in ["printer", "usb", "pendrive", "wifi", "internet", "network", "sound", "audio", "troubleshoot", "battery", "camera", "mic"]):
        if "battery" in task_lower:
            return await handle_health_task(task)
        if "camera" in task_lower or "mic" in task_lower:
            return await handle_browser_help_task(task)
        return await handle_hardware_task(task)
    
    # 3. Settings / Accessibility tasks
    if any(k in task_lower for k in ["font", "text size", "contrast", "magnifier", "brightness", "display", "setting"]):
        return await handle_settings_task(task)

    # 4. Security & Maintenance
    if any(k in task_lower for k in ["scan", "virus", "defender", "update", "security", "clean", "storage", "cleanup", "pin", "password"]):
        if "pin" in task_lower or "password" in task_lower:
            return await handle_tutorial_task(task)
        if "clean" in task_lower or "storage" in task_lower or "cleanup" in task_lower:
            return await handle_maintenance_task(task)
        return await handle_security_task(task)

    # 5. Process & App Management
    if any(k in task_lower for k in ["kill", "terminate", "stop", "close", "app", "software", "process", "slow", "performance", "suspicious", "default"]):
        if "default" in task_lower:
            return await handle_browser_help_task(task)
        if "open" in task_lower or "launch" in task_lower:
             return await _launch_app_simple(task)
        return await handle_process_task(task)

    # 6. Health & SOS
    if any(k in task_lower for k in ["reminder", "remind", "sos", "emergency"]):
        return await handle_health_task(task)

    # 7. Diagnostics
    if any(k in task_lower for k in ["crash", "blue screen", "bsod", "event log"]):
        return await handle_diagnostic_task(task)

    # 8. Browser Help (fallback)
    if "tab" in task_lower or "recovery" in task_lower:
        return await handle_browser_help_task(task)

    # 9. Tutorials
    if "tutorial" in task_lower or "how to" in task_lower or "guide" in task_lower:
        return await handle_tutorial_task(task)

    # Fallback to App Launching
    if "open" in task_lower or "launch" in task_lower:
        return await _launch_app_simple(task)
    
    return f"I understand you want to '{task}', but I'm not sure how to do that yet. I can help with files, security scans, closing apps, and system settings."

async def _launch_app_simple(task: str) -> str:
    """Uses PyAutoGUI to launch an app via the Start menu."""
    try:
        # Extract app name (naive)
        app_name = task.replace("open", "").replace("launch", "").strip()
        
        pyautogui.press('win')
        await asyncio.sleep(0.5)
        pyautogui.typewrite(app_name)
        await asyncio.sleep(1.0)
        pyautogui.press('enter')
        
        return f"I've attempted to open {app_name} for you. It should appear on your screen shortly."
    except Exception as e:
        return f"I tried to open the app but ran into an error: {str(e)}"
