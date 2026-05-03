"""
window_module.py — Advanced window management for AutoOS.
Supports snapping windows to left/right, maximizing, and centering.
"""
from __future__ import annotations
import logging
import asyncio
try:
    import win32gui
    import win32con
    import win32api
except ImportError:
    win32gui = None
    win32con = None
    win32api = None

logger = logging.getLogger("AutoOS.window_module")

async def run(task: str, entities: list[str], action_params: dict) -> str:
    if not win32gui:
        return "Window management is only available on Windows."

    app_name = action_params.get("app_name") or (entities[0] if entities else "")
    
    # Handle aliases for common apps
    if app_name.lower() in ["antigravity", "autoos", "assistant", "this window"]:
        app_name = "AutoOS Assistant"
    elif app_name.lower() == "brave":
        app_name = "Brave"

    action = action_params.get("action", "").lower()
    
    if not app_name and action != "tile_all":
        return "I need to know which app you want me to manage."

    # Find the window handle (HWND)
    hwnd = _find_window(app_name)
    if not hwnd and action != "tile_all":
        return f"Could not find an open window for '{app_name}'."

    screen_w = win32api.GetSystemMetrics(0)
    screen_h = win32api.GetSystemMetrics(1)
    # Account for taskbar (approximate)
    work_h = screen_h - 40 

    if action == "snap_left":
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, screen_w // 2, work_h, win32con.SWP_SHOWWINDOW)
        return f"Snapped '{app_name}' to the left half of the screen."

    elif action == "snap_right":
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, screen_w // 2, 0, screen_w // 2, work_h, win32con.SWP_SHOWWINDOW)
        return f"Snapped '{app_name}' to the right half of the screen."

    elif action == "maximize":
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        return f"Maximized '{app_name}'."

    elif action == "minimize":
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        return f"Minimized '{app_name}'."

    elif action == "restore":
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        return f"Restored '{app_name}' window."

    return f"I don't know how to perform the action '{action}' on windows yet."


def _find_window(title_substring: str):
    """Find the first window handle matching the title substring."""
    result = {"hwnd": None}
    
    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).lower()
            if title_substring.lower() in title:
                result["hwnd"] = hwnd
                return False
        return True
    
    try:
        win32gui.EnumWindows(callback, None)
    except: pass
    return result["hwnd"]
