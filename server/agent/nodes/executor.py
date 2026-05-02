from typing import Any
import asyncio
import subprocess
import time
import os
import re
import logging
from langchain_core.runnables import RunnableConfig
from server.agent.state import AgentState
from server.agent.tools.browser_tool import run_browser_task
from server.agent.bus import emit_event
from server.agent.modules import app_module

logger = logging.getLogger("AutoOS.executor")

# ─────────────────────────────────────────
# DIRECT OS EXECUTOR — No LLM, No Hanging
# ─────────────────────────────────────────

async def launch_app(app_name: str) -> str:
    try:
        # Use the robust app_module to find and launch the app
        # This handles Registry, Shortcuts, and Start Menu
        result = await app_module.run(app_name, [app_name], {"app_name": app_name})
        return result
    except Exception as e:
        return f"Failed to open {app_name}: {e}"

def open_folder(folder_name: str) -> str:
    special = {
        "downloads": os.path.expanduser("~/Downloads"),
        "desktop": os.path.expanduser("~/Desktop"),
        "documents": os.path.expanduser("~/Documents"),
        "pictures": os.path.expanduser("~/Pictures"),
        "music": os.path.expanduser("~/Music"),
        "videos": os.path.expanduser("~/Videos"),
    }
    path = special.get(folder_name.lower().strip(), folder_name)
    try:
        subprocess.Popen(f'explorer "{path}"', shell=True)
        time.sleep(1.5)
        return f"Opened {path} in File Explorer."
    except Exception as e:
        return f"Failed to open folder: {e}"

async def create_file_or_folder(name: str, folder_name: str = "desktop", content: str = "", is_folder: bool = False) -> str:
    # Resolve the true Windows path (handling OneDrive)
    user_path = os.path.expanduser("~")
    
    # Priority: 1. OneDrive 2. Local
    candidates = [
        os.path.join(user_path, "OneDrive", folder_name.capitalize()),
        os.path.join(user_path, folder_name.capitalize()),
        os.path.join(user_path, "Desktop") # Fallback
    ]
    
    base_path = next((c for c in candidates if os.path.exists(c)), os.path.expanduser("~/Desktop"))
    
    # Sanitize the name: Windows doesn't allow these: < > : " / \ | ? *
    clean_name = re.sub(r'[<>:"/\\|?*]', '', name).strip()
    full_path = os.path.join(base_path, clean_name)
    
    try:
        if is_folder:
            os.makedirs(full_path, exist_ok=True)
            if os.path.exists(full_path):
                # Open explorer and highlight the new folder
                subprocess.Popen(f'explorer /select,"{full_path}"', shell=True)
                await asyncio.sleep(1.5)
                
                # Use "Desktop DOM" (Window Management) to focus and refresh
                try:
                    import pygetwindow as gw
                    import pyautogui
                    # Try to find the explorer window
                    title = os.path.basename(base_path)
                    wa_windows = [w for w in gw.getWindowsWithTitle(title) if w.visible]
                    if wa_windows:
                        wa_windows[0].activate()
                        pyautogui.press('f5') # Refresh the view
                except:
                    pass
                    
                return f"Successfully created folder at: {full_path}"
            return f"Failed to verify folder creation at {full_path}"
        else:
            with open(full_path, "w") as f:
                f.write(content)
            # Open explorer and highlight the new file
            subprocess.Popen(f'explorer /select,"{full_path}"', shell=True)
            return f"Successfully created file at: {full_path}"
    except Exception as e:
        return f"File creation failed: {e}"

def compute_in_calculator(expression: str) -> str:
    try:
        import pyautogui
        subprocess.Popen("calc.exe", shell=True)
        time.sleep(2.5)
        # Clean expression - only allow valid calculator chars
        clean = re.sub(r'[^0-9+\-*/().]', '', expression)
        pyautogui.write(clean, interval=0.1)
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)
        # Also compute answer in Python
        answer = eval(clean)
        return f"Opened calculator and entered '{clean}'. The answer is {answer}."
    except Exception as e:
        return f"Calculator failed: {e}"

def check_disk_space() -> str:
    import shutil
    total, used, free = shutil.disk_usage("/")
    return (
        f"Your disk — "
        f"Total: {total // (2**30)} GB, "
        f"Used: {used // (2**30)} GB, "
        f"Free: {free // (2**30)} GB"
    )

def get_battery_status() -> str:
    try:
        import psutil
        b = psutil.sensors_battery()
        if b:
            status = "charging" if b.power_plugged else "not charging"
            return f"Battery is at {b.percent:.0f}% and is {status}."
        return "No battery found (desktop PC)."
    except Exception as e:
        return f"Could not check battery: {e}"

def check_wifi() -> str:
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True, timeout=5
        )
        if "State" in result.stdout:
            lines = [l for l in result.stdout.splitlines() if "State" in l or "SSID" in l or "Signal" in l]
            return "Wi-Fi Status: " + " | ".join(l.strip() for l in lines)
        return "Wi-Fi adapter not found or no connection."
    except Exception as e:
        return f"Wi-Fi check failed: {e}"

def check_bluetooth() -> str:
    try:
        # Open settings as requested by the user
        os.startfile("ms-settings:bluetooth")
        # Run PowerShell to get devices
        cmd = 'Get-PnpDevice -Class Bluetooth | Select-Object FriendlyName,Status | ConvertTo-Json'
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True, text=True, timeout=10
        )
        if not result.stdout.strip():
            return "No Bluetooth devices detected."
        import json
        devices = json.loads(result.stdout)
        if isinstance(devices, dict): devices = [devices]
        lines = [f"Found {len(devices)} Bluetooth device(s):"]
        for d in devices[:10]:
            lines.append(f"• {d.get('FriendlyName')} ({d.get('Status')})")
        return "\n".join(lines)
    except Exception as e:
        return f"Bluetooth check failed: {e}"

def open_settings(section: str = "") -> str:
    try:
        uri_map = {
            "display": "ms-settings:display",
            "sound": "ms-settings:sound",
            "bluetooth": "ms-settings:bluetooth",
            "wifi": "ms-settings:network-wifi",
            "update": "ms-settings:windowsupdate",
            "privacy": "ms-settings:privacy",
            "storage": "ms-settings:storagesense",
            "": "ms-settings:",
        }
        uri = uri_map.get(section.lower().strip(), "ms-settings:")
        os.startfile(uri)
        time.sleep(1.5)
        return f"Opened Windows Settings{(' - ' + section) if section else ''}."
    except Exception as e:
        return f"Failed to open settings: {e}"

async def open_whatsapp_chat(contact_name: str) -> str:
    try:
        import pyautogui
        # Try to get window management for focus
        try:
            import pygetwindow as gw
        except:
            gw = None

        # 1. Launch/Show WhatsApp
        await launch_app("whatsapp")
        await asyncio.sleep(5) # Give it plenty of time to come to front
        
        # 2. Force window focus if possible
        if gw:
            try:
                wa_windows = [w for w in gw.getWindowsWithTitle('WhatsApp') if w.visible]
                if wa_windows:
                    wa_windows[0].activate()
                    await asyncio.sleep(1)
            except:
                pass # Fail silently if activation fails
        
        # 3. Search for the contact (Ctrl+F)
        # We try twice to be sure
        for _ in range(2):
            pyautogui.hotkey('ctrl', 'f')
            await asyncio.sleep(0.5)
        
        pyautogui.write(contact_name, interval=0.1)
        await asyncio.sleep(2) # Wait for search results
        
        # 4. Open the chat
        pyautogui.press('enter')
        await asyncio.sleep(1)
        return f"Opened WhatsApp and focused on '{contact_name}'."
    except Exception as e:
        return f"Could not open specific chat: {e}"

async def send_whatsapp_message(contact_name: str, message: str) -> str:
    try:
        import pyautogui
        # 1. Open the chat first (using our existing robust navigation)
        nav_result = await open_whatsapp_chat(contact_name)
        if "Could not" in nav_result:
            return nav_result
            
        await asyncio.sleep(1.5) # Wait for UI to settle
        
        # 2. Type the message and send
        pyautogui.write(message, interval=0.05)
        await asyncio.sleep(0.5)
        pyautogui.press('enter')
        
        # 3. Take a screenshot for visual confirmation
        os.makedirs("server/screenshots", exist_ok=True)
        pyautogui.screenshot("server/screenshots/whatsapp_sent.png")
        
        return f"Sent message to '{contact_name}': \"{message}\". (Verification screenshot saved)"
    except Exception as e:
        return f"Failed to send message: {e}"

# ─────────────────────────────────────────
# SMART TASK PARSER — No LLM needed
# ─────────────────────────────────────────

async def parse_and_execute_os_task(task: str) -> str:
    t = task.lower().strip()
    
    # Calculator with computation
    calc_match = re.search(r'(\d+[\s]*[+\-*/][\s]*\d+[\s]*[+\-*/\d\s]*)', task)
    if any(w in t for w in ["calculator", "calculate", "compute", "math"]) or calc_match:
        if calc_match:
            expr = calc_match.group(1).replace(" ", "")
            return compute_in_calculator(expr)
        else:
            return await launch_app("calculator")
    
    # Folder opening
    for folder in ["downloads", "desktop", "documents", "pictures", "music", "videos"]:
        if folder in t and any(w in t for w in ["open", "show", "go to", "navigate"]):
            return open_folder(folder)
    
    # File/Folder Creation
    # Catch "create [file/folder] [name] in/on [folder]"
    # Added [^a-zA-Z0-9]* at end to ignore trailing quotes/garbage
    create_match = re.search(r'create\s+(?:a\s+)?(file|folder)\s+(?:named\s+)?(.*?)(?:\s+(?:in|on|at)\s+(?:my\s+)?([a-zA-Z0-9\s._-]+))?[^a-zA-Z0-9]*$', t)
    if create_match:
        item_type = create_match.group(1).strip()
        item_name = create_match.group(2).strip()
        # Clean up "my " if it leaked into the name
        if item_name.endswith(" on my"): item_name = item_name[:-6].strip()
        if item_name.endswith(" in my"): item_name = item_name[:-6].strip()
        
        folder = create_match.group(3).strip() if create_match.group(3) else "desktop"
        content_match = re.search(r'with\s+(?:the\s+)?(?:text|content)\s+[\'"](.+)[\'"]', task, re.IGNORECASE)
        content = content_match.group(1) if content_match else ""
        return await create_file_or_folder(item_name, folder, content, is_folder=(item_type == "folder"))

    # App launching
    # Catch "send [message] to [name] on whatsapp"
    wa_send_match = re.search(r'send\s+(.+)\s+to\s+([a-zA-Z0-9\s._-]+)\s+(?:on|in)\s+whatsapp', t)
    if wa_send_match:
        msg = wa_send_match.group(1).strip()
        contact = wa_send_match.group(2).strip()
        return await send_whatsapp_message(contact, msg)

    # Catch "open [name]'s chat in whatsapp" or "open whatsapp and navigate to [name] chat"
    wa_chat_match = re.search(r'(?:open|navigate|go to|search)\s+(?:whatsapp\s+and\s+)?(?:navigate\s+to\s+|find\s+)?([a-zA-Z0-9\s._-]+)\s+chat(?:\s+in\s+whatsapp)?', t)
    if wa_chat_match:
        return await open_whatsapp_chat(wa_chat_match.group(1).strip())

    # Catch "open [app]", "launch [app]", "start [app]"
    launch_match = re.search(r'(?:open|launch|start|run|play)\s+([a-zA-Z0-9\s._-]+)', t)
    if launch_match:
        target_app = launch_match.group(1).strip()
        # Exclude folders and settings from app launch catch-all
        if not any(f in target_app for f in ["downloads", "desktop", "documents", "pictures", "music", "videos", "settings"]):
            return await launch_app(target_app)

    # Fallback keyword match for specific common apps
    for app in ["notepad", "paint", "word", "excel", "cmd", "powershell", "taskmgr", "taskmanager", "explorer", "vlc", "spotify", "whatsapp", "chrome", "edge"]:
        if app in t:
            return await launch_app(app)
    
    # System checks
    if any(w in t for w in ["disk", "storage", "space", "memory"]):
        return check_disk_space()
    
    if any(w in t for w in ["battery", "charging", "power"]):
        return get_battery_status()
    
    if any(w in t for w in ["wifi", "wi-fi", "internet", "network", "connection"]):
        if any(w in t for w in ["turn", "on", "off", "toggle", "switch", "connect"]):
            return open_settings("wifi")
        return check_wifi()
    
    if "bluetooth" in t:
        if any(w in t for w in ["turn", "on", "off", "toggle", "switch", "connect"]):
            return open_settings("bluetooth")
        return check_bluetooth()
    
    # Settings
    for section in ["display", "sound", "bluetooth", "wifi", "update", "privacy", "storage"]:
        if section in t and any(w in t for w in ["settings", "setting", "open", "go to", "turn", "on", "off"]):
            return open_settings(section)
    if "settings" in t:
        return open_settings()

    return f"I understood this is an OS task but I'm not sure how to handle: '{task}'. Please be more specific."

# ─────────────────────────────────────────
# BROWSER EXECUTOR
# ─────────────────────────────────────────

async def browser_executor(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    task = state.get("task", "")
    
    await emit_event(config, {
        "type": "step_start",
        "description": f"Starting browser task: {task}"
    })

    try:
        result = await asyncio.wait_for(
            run_browser_task(
                task,
                headless=state.get("headless"),
                input_values=state.get("input_values"),
                max_steps=state.get("max_steps"),
            ),
            timeout=120.0
        )
    except asyncio.TimeoutError:
        result = "Browser task timed out after 2 minutes. Please try again."
    except Exception as e:
        result = f"Browser task failed: {str(e)}"

    await emit_event(config, {"type": "step_done", "description": "Completed browser task"})
    await emit_event(config, {"type": "complete", "summary": result})

    return {
        "result": result,
        "messages": [{"role": "assistant", "content": f"Browser Task Result: {result}"}]
    }

# ─────────────────────────────────────────
# OS EXECUTOR — Direct execution, no LLM
# ─────────────────────────────────────────

async def os_executor(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    task = state.get("task", "")
    t = task.lower()

    # Human-friendly status message
    if "calculator" in t or any(op in task for op in ["+", "-", "*", "/"]):
        status_msg = "Opening your calculator now..."
    elif any(f in t for f in ["downloads", "desktop", "documents", "folder"]):
        status_msg = "Opening that folder for you..."
    elif "notepad" in t:
        status_msg = "Opening Notepad for you..."
    elif "settings" in t:
        status_msg = "Opening Settings for you..."
    elif "wifi" in t or "wi-fi" in t or "internet" in t:
        status_msg = "Checking your internet connection..."
    elif "battery" in t:
        status_msg = "Checking your battery status..."
    elif "disk" in t or "storage" in t:
        status_msg = "Checking your storage space..."
    else:
        status_msg = f"Working on: {task}"

    await emit_event(config, {
        "type": "classification",
        "category": "os",
        "description": status_msg
    })

    await emit_event(config, {
        "type": "step_start",
        "description": status_msg
    })

    try:
        # Run directly since it's already async and fast
        result = await parse_and_execute_os_task(task)
    except Exception as e:
        result = f"Something went wrong: {str(e)}"

    await emit_event(config, {
        "type": "step_done",
        "description": f"Done! {result}"
    })
    await emit_event(config, {"type": "complete", "summary": result})

    return {
        "result": result,
        "messages": [{"role": "assistant", "content": result}]
    }
