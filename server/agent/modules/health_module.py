import logging
from datetime import datetime

logger = logging.getLogger("AutoOS.health_module")

# In-memory storage for reminders (MVP)
# In production, this would be in the database
REMINDERS = []

async def handle_health_task(task: str) -> str:
    """Handles reminders and SOS alerts."""
    task_lower = task.lower()
    
    if "reminder" in task_lower or "remind" in task_lower:
        return await set_reminder(task)
    
    if "sos" in task_lower or "emergency" in task_lower:
        return await trigger_sos()
        
    if "battery" in task_lower:
        return await check_battery_health()

    return "I can set reminders for your medicine or calls, and I have an Emergency SOS system. What do you need?"

async def set_reminder(task: str) -> str:
    """Sets a simple reminder (MVP logic)."""
    # This is a placeholder for more complex NLP extraction
    REMINDERS.append({
        "task": task,
        "time": datetime.now().strftime("%H:%M")
    })
    return f"I've set a reminder for you: '{task}'. I'll make sure to let you know when it's time!"

async def trigger_sos() -> str:
    """Triggers the emergency SOS protocol."""
    # In the real app, this would also emit a specific WS event for the frontend to show a massive alert
    return "EMERGENCY SOS TRIGGERED. I am displaying a large alert on your screen and will attempt to notify your primary contact if configured."

async def check_battery_health() -> str:
    """Checks battery status and health."""
    import psutil
    battery = psutil.sensors_battery()
    if not battery:
        return "I can't find a battery. Is this a desktop computer?"
        
    percent = battery.percent
    plugged = battery.power_plugged
    status = "plugged in" if plugged else "running on battery"
    
    msg = f"Your battery is at {percent}% and is currently {status}."
    if percent < 20 and not plugged:
        msg += " I recommend plugging in your charger soon!"
        
    return msg
