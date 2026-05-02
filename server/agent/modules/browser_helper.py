import logging
import subprocess

logger = logging.getLogger("AutoOS.browser_helper")

async def handle_browser_help_task(task: str) -> str:
    """Handles browser-specific help tasks."""
    task_lower = task.lower()
    
    if "tab" in task_lower or "recovery" in task_lower:
        return "I can't directly see your browser tabs yet, but usually you can press 'Ctrl + Shift + T' to reopen your last closed tab. Would you like me to open your browser for you?"
    
    if "default" in task_lower:
        return await open_default_apps_settings()
        
    if "camera" in task_lower or "mic" in task_lower:
        return await open_privacy_settings()

    return "I can help you with browser settings or checking your camera and microphone permissions."

async def open_default_apps_settings() -> str:
    """Opens the Default Apps settings page."""
    try:
        subprocess.Popen("start ms-settings:defaultapps", shell=True)
        return "I've opened the Default Apps settings for you. You can change your preferred browser or PDF viewer there."
    except Exception:
        return "I couldn't open the settings page. You can find it by searching for 'Default apps' in the Start menu."

async def open_privacy_settings() -> str:
    """Opens Privacy settings for Camera/Mic."""
    try:
        subprocess.Popen("start ms-settings:privacy-webcam", shell=True)
        return "I've opened your Camera privacy settings. Please make sure 'Allow apps to access your camera' is turned on."
    except Exception:
        return "I couldn't open the privacy settings. You can find them under Settings > Privacy & Security > Camera."
