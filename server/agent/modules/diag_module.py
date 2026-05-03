"""
diag_module.py — System diagnostics and crash explanation for AutoOS.
Uses action_params.check_type from the planner.
"""
from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger("AutoOS.diag_module")


async def run(task: str, entities: list[str], action_params: dict) -> str:
    check_type: str = action_params.get("check_type", "").lower()
    task_lower = task.lower()

    if check_type == "crash" or any(w in task_lower for w in ("crash", "blue screen", "bsod", "error", "event log")):
        return await _explain_crashes()
    if check_type == "performance" or any(w in task_lower for w in ("slow", "performance", "speed", "lag", "freez")):
        return await _performance_check()
    if check_type == "recycle_bin" or any(w in task_lower for w in ("recycle", "trash", "deleted")):
        return await _recycle_bin_info()
    
    # Redirection for misclassified network tasks
    if any(w in task_lower for w in ("wifi", "wi-fi", "network", "internet", "signal")):
        from agent.modules import hardware_module
        return await hardware_module.run(task, entities, {"device_type": "wifi"})

    # If we are here, we aren't sure exactly what the user wants to diagnose
    if check_type or task_lower:
        # Run a quick check but preface it correctly
        health = await _performance_check()
        return (
            f"I wasn't sure exactly what you wanted to diagnose, so I ran a general system health check for you:\n\n"
            f"{health}\n\n"
            "Is there a specific issue (like a crash or a slow app) you'd like me to look into?"
        )

    return await _performance_check()


import asyncio
import win32evtlog
import win32evtlogutil

async def _explain_crashes() -> str:
    """Query system logs in a background thread."""
    return await asyncio.to_thread(_explain_crashes_sync)


def _explain_crashes_sync() -> str:
    """Synchronous implementation of the event log query."""
    try:
        # Use direct Windows API for instant event log access
        server = 'localhost'
        log_type = 'System'
        
        # Read the last 100 records and filter for the 5 most recent Errors
        handle = win32evtlog.OpenEventLog(server, log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        
        events = []
        count = 0
        
        # We might need to read multiple batches to find 5 errors
        for _ in range(10): # Limit iterations to prevent hanging
            records = win32evtlog.ReadEventLog(handle, flags, 0)
            if not records:
                break
            for record in records:
                if record.EventType == win32evtlog.EVENTLOG_ERROR_TYPE:
                    # Get the message - might be slow for some sources, but still faster than PS
                    try:
                        msg = win32evtlogutil.SafeGetEventMessage(record)
                    except:
                        msg = "Detailed message not available."
                        
                    events.append({
                        "TimeGenerated": record.TimeGenerated.Format(),
                        "Source": record.SourceName,
                        "Message": msg[:200]
                    })
                    count += 1
                    if count >= 5:
                        break
            if count >= 5:
                break
        
        win32evtlog.CloseEventLog(handle)

        if not events:
            return "Good news — I checked your system logs and did not find any recent crashes or serious errors."

        lines = [f"Found {len(events)} recent system error(s):\n"]
        for e in events:
            lines.append(f"  [{e['TimeGenerated']}] {e['Source']}: {e['Message']}...")

        lines.append(
            "\nIf your computer has been crashing or restarting unexpectedly, "
            "please let me know and I can help troubleshoot further."
        )
        return "\n".join(lines)
    except Exception as exc:
        return f"Could not read system logs via Win32 API: {exc}"


async def _performance_check() -> str:
    try:
        import psutil
        
        # Start CPU check (non-blocking for now if interval is small, 
        # but let's run others while it waits)
        # psutil.cpu_percent with interval=1 is blocking.
        # We can run disk and memory checks in parallel.
        
        loop = asyncio.get_event_loop()
        
        # Run CPU check in a thread to not block the event loop
        cpu_task = loop.run_in_executor(None, psutil.cpu_percent, 0.5)
        
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("C:\\")
        
        cpu = await cpu_task
        
        mem_pct = mem.percent
        disk_pct = disk.percent
        disk_free_gb = disk.free / (1024 ** 3)

        issues = []
        if cpu > 80:
            issues.append(f"CPU is very busy ({cpu:.0f}%) — some program may be using a lot of power.")
        if mem_pct > 85:
            issues.append(f"Memory is almost full ({mem_pct:.0f}%) — try closing some apps.")
        if disk_pct > 90:
            issues.append(f"Your C: drive is almost full ({disk_free_gb:.1f} GB free) — consider deleting old files.")

        if not issues:
            return (
                f"Your computer looks healthy.\n"
                f"  CPU usage: {cpu:.0f}%\n"
                f"  Memory used: {mem_pct:.0f}%\n"
                f"  Disk free: {disk_free_gb:.1f} GB"
            )

        return "Health check results:\n" + "\n".join(f"  - {i}" for i in issues)
    except Exception as exc:
        return f"Could not check performance: {exc}"


async def _recycle_bin_info() -> str:
    try:
        # Fast ctypes check for item count
        import ctypes
        from ctypes import wintypes

        class SHQUERYRBINFO(ctypes.Structure):
            _fields_ = [
                ('cbSize', wintypes.DWORD),
                ('i64Size', ctypes.c_int64),
                ('i64NumItems', ctypes.c_int64)
            ]

        rb_info = SHQUERYRBINFO()
        rb_info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
        
        # SHQueryRecycleBinW returns 0 (S_OK) on success
        res = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(rb_info))
        
        if res == 0 and rb_info.i64NumItems == 0:
            return "Your Recycle Bin is empty."

        # If not empty, use PowerShell for detailed listing (could be optimized with COM later)
        result = subprocess.run(
            [
                "powershell", "-Command",
                "$shell = New-Object -ComObject Shell.Application; "
                "$bin = $shell.Namespace(10); "
                "$bin.Items() | Select-Object -ExpandProperty Name | ConvertTo-Json"
            ],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0 or not result.stdout.strip():
            # Fallback if PowerShell fails but we know it's not empty
            return f"There are {rb_info.i64NumItems} items in your Recycle Bin (approx {rb_info.i64Size / (1024*1024):.1f} MB)."

        import json
        try:
            items = json.loads(result.stdout)
            if isinstance(items, str):
                items = [items]
        except json.JSONDecodeError:
            return f"There are {rb_info.i64NumItems} items in your Recycle Bin but I could not list them."

        lines = [f"Recycle Bin contains {len(items)} item(s) (approx {rb_info.i64Size / (1024*1024):.1f} MB):\n"]
        for item in items[:15]:
            lines.append(f"  {item}")
        if len(items) > 15:
            lines.append(f"  ... and {len(items) - 15} more.")
        lines.append("\nTo restore a file, open the Recycle Bin on your desktop and right-click the file.")
        return "\n".join(lines)
    except Exception as exc:
        return f"Could not check Recycle Bin: {exc}"
