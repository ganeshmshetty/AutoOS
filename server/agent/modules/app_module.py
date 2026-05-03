"""
app_module.py — Smart application launcher for AutoOS.

Uses action_params.search_aliases from the planner for precise matching.

Strategy (in priority order):
  1. Windows Registry App Paths
  2. Direct .exe search using search_aliases across common install dirs
  3. Start Menu / Desktop shortcut (.lnk) search
  4. Shell Execute with the clean app name / URI scheme
  5. Clipboard-paste into Start Menu (avoids typewrite char-by-char bug)
"""
from __future__ import annotations

import asyncio
import logging
import os
import subprocess
try:
    import winreg
except ImportError:
    winreg = None
import json
from pathlib import Path
try:
    import win32gui
    import win32con
    import win32com.client
    import pythoncom
except ImportError:
    win32gui = None
    win32con = None
    win32com = None
    pythoncom = None

import pyautogui

logger = logging.getLogger("AutoOS.app_module")

_CACHE_FILE = Path("server/data/apps_cache.json")

_SEARCH_ROOTS = [
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")),
    Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs",
    Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    Path(r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"),
    Path(os.path.expanduser("~")) / "Desktop",
    Path(os.path.expanduser("~")) / "AppData" / "Local",
]


async def run(task: str, entities: list[str], action_params: dict) -> str:
    # Prefer structured params from the planner
    app_name: str = action_params.get("app_name") or (entities[0] if entities else task)
    aliases: list[str] = action_params.get("search_aliases") or [app_name]

    logger.info("Launching app: %r aliases=%s", app_name, aliases)

    strategies = [
        lambda: _try_cache(aliases),
        lambda: _try_search_indexer(aliases),
        lambda: _try_registry(aliases),
        lambda: _try_direct_search(aliases),
        lambda: _try_shortcut_search(aliases),
        lambda: _try_shell_execute(app_name, aliases),
        lambda: _try_start_menu_search(app_name),
    ]

    # Special handling for app interaction (e.g. calculation)
    action: str = action_params.get("action", "").lower()
    input_text: str = action_params.get("input", "")
    target: str = action_params.get("target", "")

    for strategy in strategies:
        result = await strategy()
        if result["success"]:
            logger.info("Launch succeeded via %s", result.get("method", "unknown"))
            
            if action == "interact" or input_text or action == "send_message" or "whatsapp" in app_name.lower():
                await asyncio.sleep(1.5) # Reduced wait time
                # Attempt instant focus via Win32 before interaction
                _focus_window(app_name)
                return await _interact_with_app(result["message"], input_text, app_name, entities, action, target)
            
            return result["message"]

    return (
        f"Could not find '{app_name}' on your computer. "
        "Make sure it is installed and try again."
    )


async def _try_cache(aliases: list[str]) -> dict:
    if not _CACHE_FILE.exists():
        return {"success": False}
    try:
        with open(_CACHE_FILE, "r") as f:
            cache = json.load(f)
        
        terms = [a.lower().replace(" ", "").replace("-", "").replace("_", "") for a in aliases]
        for term in terms:
            if term in cache:
                path = Path(cache[term])
                if path.exists():
                    if path.suffix.lower() == ".lnk":
                        os.startfile(str(path))
                    else:
                        subprocess.Popen([str(path)], shell=False)
                    return {
                        "success": True, "method": "cache",
                        "message": f"Launched {aliases[0]} from cache.",
                    }
    except Exception as exc:
        logger.debug("Cache read error: %s", exc)
    return {"success": False}


def _update_cache(term: str, path: Path):
    cache = {}
    if _CACHE_FILE.exists():
        try:
            with open(_CACHE_FILE, "r") as f:
                cache = json.load(f)
        except: pass
    
    cache[term] = str(path)
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except: pass


async def _try_search_indexer(aliases: list[str]) -> dict:
    """Query the Windows Search Indexer in a background thread."""
    if not win32com: return {"success": False}
    return await asyncio.to_thread(_search_indexer_sync, aliases)


def _search_indexer_sync(aliases: list[str]) -> dict:
    """Synchronous implementation of the indexer query."""
    try:
        pythoncom.CoInitialize()
        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.Open("Provider=Search.CollatorDSO;Extended Properties='Application=Windows';")
        rs = win32com.client.Dispatch("ADODB.Recordset")
        
        clean_aliases = [a.replace("'", "''") for a in aliases]
        
        for alias in clean_aliases:
            query = (
                "SELECT System.ItemPathDisplay FROM SystemIndex "
                f"WHERE (System.ItemNameDisplay LIKE '%{alias}%' OR System.FileName LIKE '%{alias}%') "
                "AND (System.ItemType = '.exe' OR System.ItemType = '.lnk') "
                "ORDER BY System.Search.Rank DESC"
            )
            
            try:
                rs.Open(query, conn)
                if not rs.EOF:
                    path = rs.Fields.Item("System.ItemPathDisplay").Value
                    if path and Path(path).exists():
                        if path.lower().endswith(".lnk"):
                            os.startfile(path)
                        else:
                            subprocess.Popen([path], shell=False)
                        
                        _update_cache(alias.lower().replace(" ", ""), Path(path))
                        return {
                            "success": True, "method": "indexer",
                            "message": f"Found {aliases[0]} via Windows Search."
                        }
            except Exception:
                continue
            finally:
                if rs.State == 1: rs.Close()
                
        conn.Close()
    except Exception as exc:
        logger.debug("Indexer search failed: %s", exc)
    finally:
        pythoncom.CoUninitialize()
        
    return {"success": False}


async def _try_registry(aliases: list[str]) -> dict:
    if not winreg:
        return {"success": False}
    for alias in aliases:
        exe = alias if alias.lower().endswith(".exe") else alias + ".exe"
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                key_path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe}"
                with winreg.OpenKey(hive, key_path) as key:
                    exe_path, _ = winreg.QueryValueEx(key, "")
                    if exe_path and Path(exe_path).exists():
                        subprocess.Popen([exe_path], shell=False)
                        return {
                            "success": True, "method": "registry",
                            "message": f"Launched {aliases[0]} successfully.",
                        }
            except FileNotFoundError:
                continue
            except Exception as exc:
                logger.debug("Registry key error: %s", exc)
    return {"success": False}


async def _try_direct_search(aliases: list[str]) -> dict:
    """Walk install dirs looking for exes matching any alias."""
    terms = [a.lower().replace(" ", "").replace("-", "").replace("_", "") for a in aliases]
    candidates: list[Path] = []

    for root in _SEARCH_ROOTS:
        if not root.exists():
            continue
        try:
            # Only search 2 levels deep to avoid hanging
            for p in root.iterdir():
                if p.is_dir():
                    try:
                        for exe in p.glob("*.exe"):
                            stem = exe.stem.lower().replace(" ", "").replace("-", "").replace("_", "")
                            if any(t in stem or stem in t for t in terms):
                                candidates.append(exe)
                    except: continue
                elif p.suffix.lower() == ".exe":
                    stem = p.stem.lower().replace(" ", "").replace("-", "").replace("_", "")
                    if any(t in stem or stem in t for t in terms):
                        candidates.append(p)
        except Exception:
            continue

    if not candidates:
        return {"success": False}

    best = min(candidates, key=lambda p: len(str(p)))
    logger.debug("Direct search matched: %s", best)
    subprocess.Popen([str(best)], shell=False)
    
    # Cache the result
    for term in terms:
        _update_cache(term, best)

    return {
        "success": True, "method": "direct_search",
        "message": f"Launched {aliases[0]} from {best.parent.name}.",
    }


async def _try_shortcut_search(aliases: list[str]) -> dict:
    """Find and launch apps via .lnk files using the Indexer."""
    return await asyncio.to_thread(_try_shortcut_indexer_sync, aliases)


def _try_shortcut_indexer_sync(aliases: list[str]) -> dict:
    """Synchronous implementation of shortcut indexer search."""
    try:
        pythoncom.CoInitialize()
        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.Open("Provider=Search.CollatorDSO;Extended Properties='Application=Windows';")
        rs = win32com.client.Dispatch("ADODB.Recordset")
        
        terms = [a.lower() for a in aliases]
        kw_clauses = [f"System.FileName LIKE '%{t.replace(\"'\", \"''\")}%'" for t in terms]
        
        query = (
            "SELECT TOP 5 System.ItemNameDisplay, System.ItemPathDisplay "
            "FROM SystemIndex "
            f"WHERE ({' OR '.join(kw_clauses)}) "
            "AND System.FileExtension = '.lnk' "
            "ORDER BY System.Search.Rank DESC"
        )
        
        try:
            rs.Open(query, conn)
            if not rs.EOF:
                name = rs.Fields.Item("System.ItemNameDisplay").Value
                path = rs.Fields.Item("System.ItemPathDisplay").Value
                
                os.startfile(path)
                
                # Cache it
                for t in terms:
                    if t in name.lower():
                        _update_cache(t.replace(" ", "").replace("-", "").replace("_", ""), Path(path))

                return {
                    "success": True, "method": "shortcut_indexer",
                    "message": f"Launched {aliases[0]} via Windows Search shortcut.",
                }
        finally:
            if rs.State == 1: rs.Close()
            conn.Close()
            
    except Exception as exc:
        logger.debug("Shortcut indexer search failed: %s", exc)
        
    return {"success": False}


async def _try_shell_execute(app_name: str, aliases: list[str]) -> dict:
    # Modern UWP Apps and URI schemes
    uri_map = {
        "calculator": "calc:",
        "calc": "calc:",
        "photos": "ms-photos:",
        "photo": "ms-photos:",
        "settings": "ms-settings:",
        "clock": "ms-clock:",
        "calendar": "outlookcal:",
        "mail": "outlookmail:",
        "store": "ms-windows-store:",
        "weather": "bingweather:",
        "whatsapp": "whatsapp:",
        "spotify": "spotify:",
        "edge": "microsoft-edge:",
        "browser": "https://google.com",
    }
    
    potential_uris = []
    # Fuzzy match aliases against uri_map
    for alias in aliases + [app_name]:
        a_low = alias.lower().strip()
        # Direct match
        if a_low in uri_map:
            potential_uris.append(uri_map[a_low])
        # Fuzzy match (e.g. "claculator" -> "calculator")
        else:
            for key, uri in uri_map.items():
                if a_low in key or key in a_low:
                    potential_uris.append(uri)
                    break

    candidates = potential_uris + [app_name] + aliases + [
        "calc.exe", "mspaint.exe", "notepad.exe",
        app_name.lower().replace(" ", "") + ".exe",
        app_name.lower().replace(" ", "-") + ".exe",
    ]
    for candidate in candidates:
        try:
            if ":" in candidate and any(u in candidate for u in uri_map.values()):
                os.startfile(candidate)
            else:
                subprocess.Popen(candidate, shell=True)
            await asyncio.sleep(1.0)
            return {
                "success": True, "method": "shell_execute",
                "message": f"Launched {app_name}.",
            }
        except Exception as exc:
            logger.debug("Shell execute '%s' failed: %s", candidate, exc)
    return {"success": False}


async def _try_start_menu_search(app_name: str) -> dict:
    """Last resort: clipboard paste into Start Menu (avoids typewrite bug)."""
    import tkinter as tk
    try:
        root_tk = tk.Tk()
        root_tk.withdraw()
        root_tk.clipboard_clear()
        root_tk.clipboard_append(app_name)
        root_tk.update()

        pyautogui.press("win")
        await asyncio.sleep(0.7)
        pyautogui.hotkey("ctrl", "v")
        await asyncio.sleep(1.2)
        pyautogui.press("enter")
        await asyncio.sleep(0.5)
        root_tk.destroy()

        return {
            "success": True, "method": "start_menu",
            "message": f"Searched Start Menu for '{app_name}' and launched the top result.",
        }
    except Exception as exc:
        logger.warning("Start Menu fallback failed: %s", exc)
        return {"success": False}


def _focus_window(title_substring: str):
    """Instant focus using Win32 API."""
    if not win32gui: return
    
    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd).lower()
        if title_substring.lower() in title:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass
            return False
        return True
    
    try:
        win32gui.EnumWindows(callback, None)
    except Exception:
        pass


async def _interact_with_app(launch_msg: str, input_text: str, app_name: str = "", entities: list[str] = None, action: str = "", target: str = "") -> str:
    """Type text into the active window."""
    entities = entities or []
    
    if "whatsapp" in app_name.lower() and input_text:
        try:
            # If explicit target was not provided, fallback to entities
            if not target:
                target = entities[1] if len(entities) > 1 else (entities[0] if entities else "")
                if target.lower() == "whatsapp":
                    target = entities[1] if len(entities) > 1 else ""
                
            pyautogui.hotkey("ctrl", "f") # Open search in WhatsApp
            await asyncio.sleep(0.5)
            if target:
                pyautogui.write(target, interval=0.05)
                await asyncio.sleep(1.0)
                pyautogui.press("enter")
                await asyncio.sleep(0.5)
                
            pyautogui.write(input_text, interval=0.05)
            pyautogui.press("enter")
            return f"{launch_msg} Found chat '{target}' and sent: '{input_text}'"
        except Exception as exc:
            logger.warning("WhatsApp interaction failed: %s", exc)
            return f"{launch_msg} (Interaction failed: {exc})"

    if not input_text:
        return launch_msg

    try:
        # Sanitize input for calculator if needed
        # (e.g. "5 plus 5" -> "5+5=")
        processed_input = input_text.lower()
        processed_input = processed_input.replace("plus", "+").replace("minus", "-")
        processed_input = processed_input.replace("times", "*").replace("multiplied by", "*")
        processed_input = processed_input.replace("divided by", "/").replace("equals", "=")
        
        if "=" not in processed_input and any(op in processed_input for op in "+-*/"):
            processed_input += "="

        pyautogui.write(processed_input, interval=0.1)
        return f"{launch_msg} I then typed: '{processed_input}'"
    except Exception as exc:
        logger.warning("Interaction failed: %s", exc)
        return f"{launch_msg} (Interaction failed: {exc})"
