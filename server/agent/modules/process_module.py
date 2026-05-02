import psutil
import logging
from typing import List, Dict

logger = logging.getLogger("AutoOS.process_module")

async def handle_process_task(task: str) -> str:
    """Handles process termination and monitoring."""
    task_lower = task.lower()
    
    if "kill" in task_lower or "terminate" in task_lower or "stop" in task_lower or "close" in task_lower:
        return await terminate_process(task)
    
    if "suspicious" in task_lower or "performance" in task_lower or "slow" in task_lower:
        return await detect_high_resource_apps()
        
    return "I can help you close apps that are stuck or check which ones are slowing down your computer."

async def terminate_process(task: str) -> str:
    """Terminates a process by name."""
    # Simple extraction of app name
    app_name = task.lower().replace("kill", "").replace("terminate", "").replace("stop", "").replace("close", "").strip()
    
    if not app_name:
        return "Which app would you like me to close?"
        
    terminated = []
    for proc in psutil.process_iter(['name']):
        try:
            if app_name in proc.info['name'].lower():
                proc.terminate()
                terminated.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    if not terminated:
        return f"I couldn't find any running apps matching '{app_name}'."
    
    return f"I've closed {len(terminated)} instance(s) of '{app_name}'."

async def detect_high_resource_apps() -> str:
    """Identifies apps using high CPU or Memory."""
    high_cpu = []
    high_mem = []
    
    for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
        try:
            if proc.info['cpu_percent'] > 50:
                high_cpu.append(proc.info['name'])
            if proc.info['memory_percent'] > 20:
                high_mem.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    if not high_cpu and not high_mem:
        return "Everything looks normal! No apps are using an unusual amount of your computer's power."
        
    results = "I noticed a few things:\n"
    if high_cpu:
        results += f"- {', '.join(high_cpu)} is using a lot of processing power.\n"
    if high_mem:
        results += f"- {', '.join(high_mem)} is using a lot of memory.\n"
    
    results += "Would you like me to close any of these for you?"
    return results
