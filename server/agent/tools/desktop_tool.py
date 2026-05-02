"""
Desktop / OS automation tools — replaces Agent-S with practical, native OS tooling.
No visual automation (not MVP). Uses subprocess + native APIs.
"""

import asyncio
import logging
import os
import platform
import subprocess
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("AutoOS.desktop")

SYSTEM = platform.system()  # "Darwin", "Linux", "Windows"


# ─── Application Launcher ───────────────────────────────────────────────────

async def open_application(app_name: str) -> dict:
    """Open an application by name."""
    logger.info(f"Opening application: {app_name}")

    try:
        if SYSTEM == "Darwin":
            # Try common app name mappings
            app_map = {
                "safari": "Safari",
                "chrome": "Google Chrome",
                "firefox": "Firefox",
                "terminal": "Terminal",
                "finder": "Finder",
                "notes": "Notes",
                "calculator": "Calculator",
                "calendar": "Calendar",
                "mail": "Mail",
                "messages": "Messages",
                "music": "Music",
                "photos": "Photos",
                "preview": "Preview",
                "system preferences": "System Preferences",
                "system settings": "System Settings",
                "activity monitor": "Activity Monitor",
                "textedit": "TextEdit",
                "vscode": "Visual Studio Code",
                "visual studio code": "Visual Studio Code",
                "code": "Visual Studio Code",
                "slack": "Slack",
                "discord": "Discord",
                "spotify": "Spotify",
                "iterm": "iTerm",
                "iterm2": "iTerm",
            }

            resolved_name = app_map.get(app_name.lower(), app_name)

            process = await asyncio.create_subprocess_exec(
                "open", "-a", resolved_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()

            if process.returncode == 0:
                return {"success": True, "message": f"Opened {resolved_name}"}
            else:
                error = stderr.decode().strip()
                return {"success": False, "message": f"Could not open '{app_name}': {error}"}

        elif SYSTEM == "Windows":
            # Windows app name mappings
            app_map = {
                "chrome": "chrome",
                "google chrome": "chrome",
                "edge": "msedge",
                "microsoft edge": "msedge",
                "firefox": "firefox",
                "notepad": "notepad",
                "calculator": "calc",
                "calc": "calc",
                "paint": "mspaint",
                "word": "winword",
                "excel": "excel",
                "powerpoint": "powerpnt",
                "outlook": "outlook",
                "terminal": "wt",
                "cmd": "cmd",
                "powershell": "powershell",
                "vscode": "code",
                "visual studio code": "code",
                "code": "code",
                "slack": "slack",
                "discord": "discord",
                "spotify": "spotify",
            }

            resolved_name = app_map.get(app_name.lower(), app_name)
            
            # Use 'start' with an empty title to handle spaces and aliases
            # Using subprocess.Popen with shell=True is the most reliable way to use 'start'
            try:
                subprocess.Popen(f'start "" "{resolved_name}"', shell=True)
                return {"success": True, "message": f"Opened {resolved_name}"}
            except Exception as e:
                return {"success": False, "message": f"Could not open '{app_name}': {str(e)}"}

        else:
            process = await asyncio.create_subprocess_exec(
                "xdg-open", app_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return {"success": True, "message": f"Opened {app_name}"}

    except Exception as e:
        logger.error(f"Failed to open application: {e}", exc_info=True)
        return {"success": False, "message": f"Failed to open {app_name}: {str(e)}"}


# ─── System Information ──────────────────────────────────────────────────────

async def get_system_info() -> dict:
    """Get comprehensive system information: CPU, memory, disk, battery."""
    import psutil

    info = {
        "platform": SYSTEM,
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "memory_used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
        "memory_percent": psutil.virtual_memory().percent,
    }

    # Disk info
    try:
        disk = psutil.disk_usage("/")
        info["disk_total_gb"] = round(disk.total / (1024**3), 2)
        info["disk_used_gb"] = round(disk.used / (1024**3), 2)
        info["disk_free_gb"] = round(disk.free / (1024**3), 2)
        info["disk_percent"] = disk.percent
    except Exception:
        pass

    # Battery
    try:
        battery = psutil.sensors_battery()
        if battery:
            info["battery_percent"] = battery.percent
            info["battery_plugged"] = battery.power_plugged
    except Exception:
        pass

    return info


# ─── Clipboard ───────────────────────────────────────────────────────────────

async def get_clipboard() -> dict:
    """Read the current clipboard contents."""
    try:
        if SYSTEM == "Darwin":
            process = await asyncio.create_subprocess_exec(
                "pbpaste",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            text = stdout.decode("utf-8", errors="replace")
            return {"success": True, "content": text}
        elif SYSTEM == "Windows":
            import base64
            script = "[Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes((Get-Clipboard -Raw)))"
            process = await asyncio.create_subprocess_exec(
                "powershell", "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            try:
                encoded = stdout.decode().strip()
                if not encoded:
                    return {"success": True, "content": ""}
                text = base64.b64decode(encoded).decode("utf-16-le")
                return {"success": True, "content": text}
            except Exception as e:
                return {"success": False, "content": "", "error": f"Failed to decode clipboard: {str(e)}"}
        else:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"],
                capture_output=True, text=True, timeout=5,
            )
            return {"success": True, "content": result.stdout.strip()}
    except Exception as e:
        return {"success": False, "content": "", "error": str(e)}


async def set_clipboard(text: str) -> dict:
    """Set the clipboard contents."""
    try:
        if SYSTEM == "Darwin":
            process = await asyncio.create_subprocess_exec(
                "pbcopy",
                stdin=asyncio.subprocess.PIPE,
            )
            await process.communicate(input=text.encode("utf-8"))
            return {"success": True, "message": "Text copied to clipboard"}
        elif SYSTEM == "Windows":
            import base64
            encoded_text = base64.b64encode(text.encode("utf-16-le")).decode("ascii")
            script = f"$text = [System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('{encoded_text}')); Set-Clipboard -Value $text"
            process = await asyncio.create_subprocess_exec(
                "powershell", "-Command", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return {"success": True, "message": "Text copied to clipboard"}
        else:
            process = subprocess.Popen(
                ["xclip", "-selection", "clipboard"],
                stdin=subprocess.PIPE,
            )
            process.communicate(input=text.encode("utf-8"))
            return {"success": True, "message": "Text copied to clipboard"}
    except Exception as e:
        return {"success": False, "message": f"Failed to set clipboard: {str(e)}"}


# ─── Desktop Notification ───────────────────────────────────────────────────

async def send_notification(title: str, message: str) -> dict:
    """Send a desktop notification to the user."""
    try:
        if SYSTEM == "Darwin":
            script = f'display notification "{message}" with title "{title}"'
            process = await asyncio.create_subprocess_exec(
                "osascript", "-e", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return {"success": True, "message": f"Notification sent: {title}"}
        elif SYSTEM == "Windows":
            import base64
            encoded_title = base64.b64encode(title.encode("utf-16-le")).decode("ascii")
            encoded_message = base64.b64encode(message.encode("utf-16-le")).decode("ascii")
            ps_script = f"""
            $title = [System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('{encoded_title}'))
            $message = [System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String('{encoded_message}'))
            [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
            $notification = New-Object System.Windows.Forms.NotifyIcon
            $notification.Icon = [System.Drawing.SystemIcons]::Information
            $notification.BalloonTipTitle = $title
            $notification.BalloonTipText = $message
            $notification.Visible = $True
            $notification.ShowBalloonTip(5000)
            """
            process = await asyncio.create_subprocess_exec(
                "powershell", "-Command", ps_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return {"success": True, "message": f"Notification sent: {title}"}
        else:
            process = await asyncio.create_subprocess_exec(
                "notify-send", title, message,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return {"success": True, "message": f"Notification sent: {title}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to send notification: {str(e)}"}


# ─── File Operations ────────────────────────────────────────────────────────

async def list_directory(path: str = "~") -> dict:
    """List the contents of a directory."""
    target = Path(os.path.expanduser(path))
    if not target.exists():
        return {"success": False, "error": f"Path does not exist: {path}"}
    if not target.is_dir():
        return {"success": False, "error": f"Not a directory: {path}"}

    try:
        entries = []
        for item in sorted(target.iterdir()):
            if item.name.startswith("."):
                continue  # Skip hidden files for cleaner output
            entry = {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
            }
            if item.is_file():
                try:
                    stat = item.stat()
                    entry["size_bytes"] = stat.st_size
                    entry["modified"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
            entries.append(entry)

        return {
            "success": True,
            "path": str(target),
            "count": len(entries),
            "entries": entries[:50],  # Limit to 50 entries
        }
    except PermissionError:
        return {"success": False, "error": f"Permission denied: {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def read_file(path: str, max_lines: int = 100) -> dict:
    """Read the contents of a text file."""
    target = Path(os.path.expanduser(path))
    if not target.exists():
        return {"success": False, "error": f"File not found: {path}"}
    if not target.is_file():
        return {"success": False, "error": f"Not a file: {path}"}

    try:
        stat = target.stat()
        if stat.st_size > 1_000_000:  # 1MB limit
            return {"success": False, "error": "File too large (>1MB). Use terminal commands to inspect it."}

        content = target.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        truncated = len(lines) > max_lines
        if truncated:
            lines = lines[:max_lines]

        return {
            "success": True,
            "path": str(target),
            "content": "\n".join(lines),
            "total_lines": len(content.splitlines()),
            "truncated": truncated,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def write_file(path: str, content: str) -> dict:
    """Write content to a file (creates or overwrites)."""
    target = Path(os.path.expanduser(path))
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"success": True, "message": f"File written: {target}", "size_bytes": len(content.encode("utf-8"))}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def search_files(query: str, search_path: str = "~", file_type: str | None = None) -> dict:
    """Search for files by name pattern."""
    target = Path(os.path.expanduser(search_path))
    if not target.exists():
        return {"success": False, "error": f"Search path does not exist: {search_path}"}

    try:
        pattern = f"*{query}*" if file_type is None else f"*{query}*.{file_type}"
        found = []
        for item in target.rglob(pattern):
            if item.name.startswith("."):
                continue
            found.append({
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
            })
            if len(found) >= 20:
                break

        return {
            "success": True,
            "query": query,
            "results_count": len(found),
            "results": found,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── Open URL ────────────────────────────────────────────────────────────────

async def open_url(url: str) -> dict:
    """Open a URL in the default browser."""
    try:
        if SYSTEM == "Darwin":
            process = await asyncio.create_subprocess_exec("open", url)
            await process.communicate()
        elif SYSTEM == "Windows":
            subprocess.Popen(f'start "" "{url}"', shell=True)
        else:
            process = await asyncio.create_subprocess_exec("xdg-open", url)
            await process.communicate()
        return {"success": True, "message": f"Opened {url} in browser"}
    except Exception as e:
        return {"success": False, "message": f"Failed to open URL: {str(e)}"}
