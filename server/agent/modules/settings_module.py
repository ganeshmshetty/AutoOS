import os
import subprocess
import logging
import asyncio

logger = logging.getLogger("AutoOS.settings_module")

async def handle_settings_task(task: str) -> str:
    """Handles system settings and accessibility tasks."""
    task_lower = task.lower()
    
    if "font" in task_lower or "text size" in task_lower:
        return await toggle_accessibility_setting("Font size", "Display")
    
    if "contrast" in task_lower:
        return await toggle_high_contrast()
        
    if "magnifier" in task_lower:
        return await launch_magnifier()
        
    if "brightness" in task_lower:
        return await adjust_brightness(task)

    return "I can help you change your font size, turn on high contrast, or open the magnifier. What would you like to do?"

async def toggle_accessibility_setting(setting_name: str, page: str) -> str:
    """Opens the specific accessibility settings page."""
    try:
        # URI schemes for Windows Settings: https://learn.microsoft.com/en-us/windows/uwp/launch-resume/launch-settings-app
        uri = f"ms-settings:easeofaccess-{page.lower()}"
        subprocess.Popen(["start", uri], shell=True)
        return f"I've opened the {setting_name} settings for you. You can adjust them there to make things easier to see."
    except Exception as e:
        return f"I couldn't open the settings page: {str(e)}"

async def toggle_high_contrast() -> str:
    """Toggles high contrast mode (opens settings)."""
    return await toggle_accessibility_setting("High Contrast", "highcontrast")

async def launch_magnifier() -> str:
    """Launches the Windows Magnifier."""
    try:
        subprocess.Popen(["magnify.exe"])
        return "I've turned on the Magnifier for you. You can use it to zoom in on parts of the screen. Press the Windows key and '+' or '-' to zoom, and Windows and 'Esc' to turn it off."
    except Exception as e:
        return f"I couldn't start the Magnifier: {str(e)}"

async def adjust_brightness(task: str) -> str:
    """Opens brightness settings."""
    return await toggle_accessibility_setting("Brightness", "display")
