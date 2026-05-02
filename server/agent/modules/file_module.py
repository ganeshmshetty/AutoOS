import os
import glob
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("AutoOS.file_module")

async def handle_file_task(task: str) -> str:
    """Handles file-related tasks."""
    task_lower = task.lower()
    
    if "search" in task_lower or "find" in task_lower or "where" in task_lower:
        return await smart_search(task)
    
    if "recent" in task_lower or "working on" in task_lower:
        return await get_recent_files()
    
    if "download" in task_lower:
        return await find_lost_downloads()
        
    return "I'm not sure how to help with that file task yet. I can search for files, find recent ones, or look for downloads."

async def smart_search(task: str) -> str:
    """Searches for files by name or type."""
    # Simple extraction of search term
    search_term = task.lower().replace("search for", "").replace("find", "").replace("where is", "").strip()
    
    # Common locations to search
    locations = [
        Path.home() / "Documents",
        Path.home() / "Desktop",
        Path.home() / "Downloads"
    ]
    
    found_files = []
    for loc in locations:
        if not loc.exists():
            continue
        # Search recursively for matches
        for file in loc.rglob(f"*{search_term}*"):
            if file.is_file():
                found_files.append(file)
                if len(found_files) >= 5: # Limit results
                    break
        if len(found_files) >= 5:
            break
            
    if not found_files:
        return f"I couldn't find any files matching '{search_term}' in your Documents, Desktop, or Downloads."
    
    results = "I found these files:\n"
    for f in found_files:
        results += f"- {f.name} (in {f.parent})\n"
    
    return results

async def get_recent_files() -> str:
    """Lists files modified in the last 24 hours."""
    locations = [
        Path.home() / "Documents",
        Path.home() / "Desktop",
        Path.home() / "Downloads"
    ]
    
    recent_files = []
    now = datetime.now().timestamp()
    
    for loc in locations:
        if not loc.exists():
            continue
        for file in loc.glob("*"):
            if file.is_file():
                mtime = file.stat().st_mtime
                if now - mtime < 86400: # 24 hours
                    recent_files.append((file, mtime))
    
    # Sort by mtime
    recent_files.sort(key=lambda x: x[1], reverse=True)
    
    if not recent_files:
        return "I couldn't find any files you worked on recently (in the last 24 hours)."
    
    results = "Here are the files you worked on recently:\n"
    for f, _ in recent_files[:5]:
        results += f"- {f.name}\n"
    
    return results

async def find_lost_downloads() -> str:
    """Finds the most recent downloads."""
    download_dir = Path.home() / "Downloads"
    if not download_dir.exists():
        return "I couldn't find your Downloads folder."
        
    files = list(download_dir.glob("*"))
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not files:
        return "Your Downloads folder is empty."
        
    latest = files[0]
    return f"Your most recent download is '{latest.name}'. Would you like me to open it for you?"
