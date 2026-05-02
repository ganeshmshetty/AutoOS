import os
import asyncio
import pyautogui
import logging
from typing import Optional

logger = logging.getLogger("AutoOS.desktop")

async def run_os_task(task: str, mode: str = "auto") -> str:
    """
    Executes a desktop automation task.
    Modes:
    - 'simple': Uses PyAutoGUI for basic inputs
    - 'complex': Uses Agent-S for visual navigation (not fully implemented)
    - 'auto': Decides based on task complexity
    """
    logger.info(f"Executing OS task: {task}")

    # For MVP, we use a hybrid approach
    if "open" in task.lower() or "launch" in task.lower():
        return await _launch_app_simple(task)
    
    # Placeholder for Agent-S complex visual tasks
    return f"OS Task '{task}' recognized. Complex visual navigation via Agent-S is ready for implementation by Person 1."

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
        
        return f"Successfully attempted to launch {app_name} via PyAutoGUI."
    except Exception as e:
        return f"Failed to launch app: {str(e)}"
