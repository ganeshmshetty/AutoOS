import os
import subprocess
import logging

logger = logging.getLogger("AutoOS.tutorial_module")

async def handle_tutorial_task(task: str) -> str:
    """Handles OS tutorials and guided setups."""
    task_lower = task.lower()
    
    if "pin" in task_lower or "password" in task_lower or "lock" in task_lower:
        return await open_sign_in_options()
    
    if "tutorial" in task_lower or "how to" in task_lower or "guide" in task_lower:
        return await open_get_started()
        
    return "I can help you set up a PIN for security or show you basic tutorials on how to use Windows. What would you like to learn?"

async def open_sign_in_options() -> str:
    """Opens Windows Sign-in options for PIN setup."""
    try:
        subprocess.Popen("start ms-settings:signinoptions", shell=True)
        return "I've opened the Sign-in options for you. I recommend setting up a **PIN** as it's easier to remember than a long password. Look for the 'PIN (Windows Hello)' section."
    except Exception:
        return "I couldn't open the settings page. You can find it by going to Settings > Accounts > Sign-in options."

async def open_get_started() -> str:
    """Opens the Windows 'Get Started' app."""
    try:
        # Launch the 'Get Started' or 'Tips' app
        subprocess.Popen("start ms-get-started:", shell=True)
        return "I've opened the 'Get Started' app for you. It has excellent step-by-step tutorials for new Windows users. I'll stay here if you need help with anything specific!"
    except Exception:
        # Fallback to Tips app
        try:
            subprocess.Popen("start ms-tips:", shell=True)
            return "I've opened the Windows Tips app. It's a great place to learn the basics of using your computer."
        except Exception:
            return "I couldn't open the tutorial app. You can find 'Tips' or 'Get Started' in your Start menu."
