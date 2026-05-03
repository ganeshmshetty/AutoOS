"""
settings_module.py — Universal Settings Navigator for AutoOS.
Maps natural language to Windows 'ms-settings:' URI schemes.
"""
from __future__ import annotations
import os
import asyncio
import logging
import subprocess
import winreg

logger = logging.getLogger("AutoOS.settings_module")

# --- Comprehensive Settings Registry ---
# Format: "keyword": "ms-settings:uri"
SETTINGS_MAP = {
    # System
    "display": "ms-settings:display",
    "screen": "ms-settings:display",
    "resolution": "ms-settings:display",
    "brightness": "ms-settings:display",
    "sound": "ms-settings:sound",
    "audio": "ms-settings:sound",
    "notifications": "ms-settings:notifications",
    "focus": "ms-settings:quiethours",
    "power": "ms-settings:powersleep",
    "battery": "ms-settings:powersleep",
    "sleep": "ms-settings:powersleep",
    "storage": "ms-settings:storagesense",
    "multitasking": "ms-settings:multitasking",
    "activation": "ms-settings:activation",
    "recovery": "ms-settings:recovery",
    "projecting": "ms-settings:project",
    "about": "ms-settings:about",
    
    # Devices
    "bluetooth": "ms-settings:bluetooth",
    "devices": "ms-settings:bluetooth",
    "printers": "ms-settings:printers",
    "scanners": "ms-settings:printers",
    "mouse": "ms-settings:mousetouchpad",
    "touchpad": "ms-settings:devices-touchpad",
    "typing": "ms-settings:typing",
    "usb": "ms-settings:usb",
    
    # Network
    "network": "ms-settings:network",
    "wifi": "ms-settings:network-wifi",
    "ethernet": "ms-settings:network-ethernet",
    "vpn": "ms-settings:network-vpn",
    "airplane": "ms-settings:network-airplanemode",
    "hotspot": "ms-settings:network-mobilehotspot",
    "proxy": "ms-settings:network-proxy",
    
    # Personalization
    "personalization": "ms-settings:personalization",
    "background": "ms-settings:personalization-background",
    "colors": "ms-settings:colors",
    "dark mode": "ms-settings:colors",
    "themes": "ms-settings:themes",
    "lock screen": "ms-settings:lockscreen",
    "fonts": "ms-settings:fonts",
    "taskbar": "ms-settings:taskbar",
    "start menu": "ms-settings:start",
    
    # Apps
    "apps": "ms-settings:appsfeatures",
    "features": "ms-settings:appsfeatures",
    "default apps": "ms-settings:defaultapps",
    "startup": "ms-settings:startupapps",
    "offline maps": "ms-settings:maps",
    
    # Accounts
    "accounts": "ms-settings:yourinfo",
    "email": "ms-settings:emailandaccounts",
    "sign-in": "ms-settings:signinoptions",
    "password": "ms-settings:signinoptions",
    
    # Time & Language
    "time": "ms-settings:dateandtime",
    "date": "ms-settings:dateandtime",
    "language": "ms-settings:regionlanguage",
    "region": "ms-settings:regionlanguage",
    "speech": "ms-settings:speech",
    
    # Gaming
    "gaming": "ms-settings:gaming-gamebar",
    "game bar": "ms-settings:gaming-gamebar",
    "game mode": "ms-settings:gaming-gamemode",
    
    # Accessibility
    "accessibility": "ms-settings:easeofaccess",
    "ease of access": "ms-settings:easeofaccess",
    "magnifier": "ms-settings:easeofaccess-magnifier",
    "narrator": "ms-settings:easeofaccess-narrator",
    "high contrast": "ms-settings:easeofaccess-highcontrast",
    "captions": "ms-settings:easeofaccess-closedcaptioning",
    
    # Privacy & Security
    "privacy": "ms-settings:privacy",
    "security": "ms-settings:windowsdefender",
    "windows security": "ms-settings:windowsdefender",
    "location": "ms-settings:privacy-location",
    "camera": "ms-settings:privacy-camera",
    "microphone": "ms-settings:privacy-microphone",
    
    # Update
    "update": "ms-settings:windowsupdate",
    "windows update": "ms-settings:windowsupdate",
    "insider": "ms-settings:windowsinsider",
}

async def run(task: str, entities: list[str], action_params: dict) -> str:
    query = action_params.get("setting") or (entities[0] if entities else "")
    task_lower = task.lower()

    # 1. Direct Registry Match
    for keyword, uri in SETTINGS_MAP.items():
        if keyword in query.lower() or keyword in task_lower:
            os.startfile(uri)
            return f"I've opened the '{keyword.title()}' settings for you directly."

    # 2. Hardcoded logic for toggles (Registry edits)
    if "dark mode" in task_lower:
         return await _toggle_dark_mode()
    if "transparency" in task_lower:
         return await _toggle_transparency()
    
    # 3. Fallback: Generic Settings with Search focus
    os.startfile("ms-settings:")
    return "I've opened the main Windows Settings. You can find your specific setting using the search bar at the top."


async def _toggle_dark_mode() -> str:
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, 0)
        return "Dark mode has been enabled via system registry."
    except Exception as e:
        os.startfile("ms-settings:colors")
        return f"I couldn't change the registry, so I opened the Colors settings for you to toggle Dark Mode manually."

async def _toggle_transparency() -> str:
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS) as key:
            current, _ = winreg.QueryValueEx(key, "EnableTransparency")
            new_val = 0 if current == 1 else 1
            winreg.SetValueEx(key, "EnableTransparency", 0, winreg.REG_DWORD, new_val)
        status = "OFF" if new_val == 0 else "ON"
        return f"Transparency effects are now {status}."
    except Exception as e:
        os.startfile("ms-settings:colors")
        return "I've opened the Color settings where you can toggle Transparency manually."
