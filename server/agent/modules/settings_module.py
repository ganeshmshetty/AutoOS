"""
settings_module.py — System settings control for AutoOS.
Uses action_params.setting and action_params.direction from the planner.
"""
from __future__ import annotations

import asyncio
import logging
import subprocess

logger = logging.getLogger("AutoOS.settings_module")


async def run(task: str, entities: list[str], action_params: dict) -> str:
    setting: str = action_params.get("setting", "").lower()
    direction: str = action_params.get("direction", "").lower()
    task_lower = task.lower()

    # Use structured params first
    if setting in ("text_size", "font_size", "text size", "font size"):
        return await _change_text_size(direction)
    if setting in ("brightness", "screen_brightness"):
        return await _change_brightness(direction)
    if setting in ("dark_mode", "dark mode", "night_mode"):
        return await _toggle_dark_mode()
    if setting in ("high_contrast", "contrast"):
        return await _toggle_high_contrast()
    if setting in ("magnifier", "zoom"):
        return await _open_magnifier()
    if setting in ("resolution", "display"):
        return await _open_display_settings()
    if setting in ("accessibility", "ease_of_access"):
        return await _open_accessibility()

    # Fallback to keyword scan
    if any(w in task_lower for w in ("font", "text", "bigger", "larger", "size", "small", "zoom")):
        return await _change_text_size(direction or task_lower)
    if any(w in task_lower for w in ("brightness", "dim", "bright")):
        return await _change_brightness(direction or task_lower)
    if any(w in task_lower for w in ("dark mode", "dark theme", "night")):
        return await _toggle_dark_mode()
    if any(w in task_lower for w in ("contrast", "high contrast")):
        return await _toggle_high_contrast()
    if any(w in task_lower for w in ("magnif", "magnifier")):
        return await _open_magnifier()
    if any(w in task_lower for w in ("resolution", "display")):
        return await _open_display_settings()
    if any(w in task_lower for w in ("accessibility", "ease of access")):
        return await _open_accessibility()

    return await _open_settings_generic()


async def _change_text_size(direction: str) -> str:
    subprocess.Popen("ms-settings:easeofaccess-display", shell=True)
    await asyncio.sleep(0.5)
    verb = "increase" if any(w in direction for w in ("increase", "bigger", "larger", "more", "up", "boost")) else "decrease" if any(w in direction for w in ("decrease", "smaller", "less", "reduce", "down")) else "adjust"
    return (
        f"I opened the Text Size settings for you.\n"
        f"Use the slider to {verb} the text size, then click Apply."
    )


async def _change_brightness(direction: str) -> str:
    try:
        get_result = subprocess.run(
            [
                "powershell", "-Command",
                "(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness"
            ],
            capture_output=True, text=True, timeout=10
        )
        current = int(get_result.stdout.strip()) if get_result.stdout.strip().isdigit() else 50

        if any(w in direction for w in ("increase", "bright", "more", "up", "higher")):
            new_val = min(100, current + 20)
        elif any(w in direction for w in ("decrease", "dim", "less", "down", "lower", "reduce")):
            new_val = max(10, current - 20)
        else:
            new_val = 70

        subprocess.run(
            [
                "powershell", "-Command",
                f"(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods)"
                f".WmiSetBrightness(1, {new_val})"
            ],
            capture_output=True, timeout=10
        )
        return f"Screen brightness set to {new_val}%."
    except Exception:
        subprocess.Popen("ms-settings:display", shell=True)
        return "I opened Display Settings where you can adjust the brightness manually."


async def _toggle_dark_mode() -> str:
    try:
        for value_name, value in [("AppsUseLightTheme", 0), ("SystemUsesLightTheme", 0)]:
            subprocess.run(
                [
                    "reg", "add",
                    r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                    "/v", value_name, "/t", "REG_DWORD", "/d", str(value), "/f"
                ],
                capture_output=True, timeout=10
            )
        return "Dark mode has been turned on. You may need to sign out and back in for all apps to update."
    except Exception:
        subprocess.Popen("ms-settings:personalization", shell=True)
        return "I opened Personalization settings where you can switch to Dark mode."


async def _toggle_high_contrast() -> str:
    subprocess.Popen("ms-settings:easeofaccess-highcontrast", shell=True)
    return "I opened High Contrast settings. You can turn it on or choose a theme there."


async def _open_magnifier() -> str:
    try:
        subprocess.Popen("magnify.exe", shell=True)
        return (
            "Magnifier is now open.\n"
            "Use Win + Plus to zoom in, Win + Minus to zoom out.\n"
            "Press Win + Esc to close it."
        )
    except Exception as exc:
        return f"Could not open Magnifier: {exc}"


async def _open_display_settings() -> str:
    subprocess.Popen("ms-settings:display", shell=True)
    return "I opened Display Settings where you can change resolution, scale, and brightness."


async def _open_accessibility() -> str:
    subprocess.Popen("ms-settings:easeofaccess", shell=True)
    return "I opened Accessibility (Ease of Access) settings for you."


async def _open_settings_generic() -> str:
    subprocess.Popen("ms-settings:", shell=True)
    return "I opened Windows Settings for you."
