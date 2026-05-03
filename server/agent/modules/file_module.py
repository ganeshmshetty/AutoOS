"""
file_module.py — File search and file operations for AutoOS.
Uses action_params for precise filtering by keywords, file types, and time hints.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("AutoOS.file_module")

_USER_ROOTS = [
    Path.home() / "Documents",
    Path.home() / "Desktop",
    Path.home() / "Downloads",
    Path.home() / "Pictures",
    Path.home() / "Videos",
    Path.home() / "Music",
    Path.home(),
]
_MAX_RESULTS = 10

_EXT_MAP = {
    "document": [".docx", ".doc", ".pdf", ".txt", ".odt"],
    "report":   [".docx", ".doc", ".pdf", ".xlsx", ".xls"],
    "image":    [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "video":    [".mp4", ".avi", ".mkv", ".mov"],
    "spreadsheet": [".xlsx", ".xls", ".csv"],
    "presentation": [".pptx", ".ppt"],
}

_TIME_HINTS = {
    "today":      timedelta(days=1),
    "yesterday":  timedelta(days=2),
    "last_week":  timedelta(weeks=1),
    "last_month": timedelta(days=30),
    "recent":     timedelta(weeks=2),
    "old":        None,  # handled separately
    "any":        None,
}


async def run(task: str, entities: list[str], action_params: dict) -> str:
    task_lower = task.lower()
    keywords: list[str] = action_params.get("keywords") or entities or []
    file_types: list[str] = action_params.get("file_types") or []
    time_hint: str = action_params.get("time_hint", "any")
    folder: str | None = action_params.get("folder")

    # Determine the requested action (default is search)
    action: str = action_params.get("action", "search")
    
    if action == "create_folder" or (any(w in task_lower for w in ("create", "make", "new")) and "folder" in task_lower):
        target_name = (entities or keywords)[0] if (entities or keywords) else "New Folder"
        od_desktop = Path.home() / "OneDrive" / "Desktop"
        dest_root = od_desktop if od_desktop.exists() else Path.home() / "Desktop"
        if "document" in task_lower:
            od_docs = Path.home() / "OneDrive" / "Documents"
            dest_root = od_docs if od_docs.exists() else Path.home() / "Documents"
        elif "download" in task.lower(): dest_root = Path.home() / "Downloads"
        
        new_dir = dest_root / target_name
        try:
            new_dir.mkdir(parents=True, exist_ok=True)
            os.startfile(str(dest_root))
            return f"Successfully created a new folder named '{target_name}' at {dest_root}."
        except Exception as e:
            return f"Failed to create folder: {e}"

    if action == "create_file" or (any(w in task_lower for w in ("create", "make", "new")) and "file" in task_lower):
        target_name = (entities or keywords)[0] if (entities or keywords) else "new_file.txt"
        dest_root = Path.home() / "Desktop"
        if "document" in task.lower(): dest_root = Path.home() / "Documents"
        elif "download" in task.lower(): dest_root = Path.home() / "Downloads"
        
        new_file = dest_root / target_name
        try:
            new_file.touch(exist_ok=True)
            os.startfile(str(dest_root))
            return f"Successfully created a new file named '{target_name}' at {dest_root}."
        except Exception as e:
            return f"Failed to create file: {e}"

    if action == "open":
        # Resolve file name from entities or keywords
        target_name = (entities or keywords)[0] if (entities or keywords) else None
        if not target_name:
            return "Please specify a file name to open."
        # Search in Downloads folder first
        downloads = Path.home() / "Downloads"
        candidate = downloads / target_name
        if candidate.exists():
            try:
                os.startfile(str(candidate))
                return f"Opened {target_name} from Downloads."
            except Exception as e:
                return f"Failed to open {target_name}: {e}"
        # Fallback: search across indexed folders using the Indexer
        search_res = await _search_files([target_name], [], "any")
        if "Found" in search_res:
            # Try to extract the first path from the search result and open it
            try:
                # The search result format is "  name  —  path  (date)"
                first_path = search_res.split("\n")[2].split("  —  ")[1].split("  (")[0].strip()
                if Path(first_path).exists():
                    os.startfile(first_path)
                    return f"Opened {target_name} found via Windows Search."
            except Exception:
                pass
        
        return f"Could not find {target_name} to open."
    # Existing logic for other actions follows
    if not keywords and not file_types:
        if any(w in task_lower for w in ("recent", "last", "working on", "yesterday")):
            return await _recent_files(entities, file_types)
        if any(w in task_lower for w in ("download", "downloaded")):
            return await _recent_downloads()

    if folder == "downloads" or any(w in task_lower for w in ("download",)):
        return await _recent_downloads()

    if not keywords:
        return await _recent_files(entities, file_types)

    return await _search_files(keywords, file_types, time_hint)


try:
    import win32com.client
    import pythoncom
except ImportError:
    win32com = None
    pythoncom = None


async def _search_files(keywords: list[str], file_types: list[str], time_hint: str) -> str:
    """Search for files using the Windows Search Indexer for near-instant results."""
    if not win32com:
        return "Search components are not available. Please ensure pywin32 is installed."
    
    return await asyncio.to_thread(_search_indexer_files_sync, keywords, file_types, time_hint)


def _search_indexer_files_sync(keywords: list[str], file_types: list[str], time_hint: str) -> str:
    """Synchronous implementation of the indexer file search."""
    try:
        pythoncom.CoInitialize()
        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.Open("Provider=Search.CollatorDSO;Extended Properties='Application=Windows';")
        rs = win32com.client.Dispatch("ADODB.Recordset")
        
        # Build the WQL query
        # We search in SystemIndex which covers indexed locations (Docs, Desktop, etc.)
        where_clauses = []
        
        # Keyword matching on FileName
        for kw in keywords:
            clean_kw = kw.replace("'", "''")
            where_clauses.append(f"(System.FileName LIKE '%{clean_kw}%' OR System.ItemNameDisplay LIKE '%{clean_kw}%')")
            
        # File type (extension) filtering
        if file_types:
            ext_clauses = [f"System.FileExtension = '{ext.lower()}'" for ext in file_types]
            where_clauses.append(f"({' OR '.join(ext_clauses)})")
            
        # Time hint filtering
        cutoff = _resolve_time_hint(time_hint)
        if cutoff:
            # WQL dates are in 'YYYY/MM/DD HH:MM:SS' format or ISO-like
            wql_date = cutoff.strftime("%Y/%m/%d %H:%M:%S")
            where_clauses.append(f"System.DateModified > '{wql_date}'")
            
        query = (
            "SELECT System.ItemNameDisplay, System.ItemPathDisplay, System.DateModified "
            "FROM SystemIndex "
            f"WHERE {' AND '.join(where_clauses)} "
            "AND System.Kind <> 'folder' "
            "ORDER BY System.DateModified DESC"
        )
        
        try:
            rs.Open(query, conn)
            results = []
            while not rs.EOF and len(results) < _MAX_RESULTS:
                name = rs.Fields.Item("System.ItemNameDisplay").Value
                path = rs.Fields.Item("System.ItemPathDisplay").Value
                mtime = rs.Fields.Item("System.DateModified").Value
                
                # mtime from COM is usually a pywintypes.datetime
                dt_str = mtime.strftime("%d %b %Y") if hasattr(mtime, "strftime") else str(mtime)
                results.append(f"  {name}  —  {path}  ({dt_str})")
                rs.MoveNext()
                
            if not results:
                return f"No files matching '{', '.join(keywords)}' found in your indexed folders."
                
            return f"Found {len(results)} file(s) matching your request:\n\n" + "\n".join(results)
            
        finally:
            if rs.State == 1: rs.Close()
            conn.Close()
            
    except Exception as exc:
        logger.error("File indexer search failed: %s", exc)
        return f"I encountered an error searching for files: {exc}"
    finally:
        pythoncom.CoUninitialize()


async def _recent_files(entities: list[str], file_types: list[str]) -> str:
    """Retrieve the most recently modified files using the Indexer."""
    if not win32com:
        return "Search components are not available. Please ensure pywin32 is installed."
    
    return await asyncio.to_thread(_recent_files_sync, file_types)


def _recent_files_sync(file_types: list[str]) -> str:
    """Synchronous implementation of the recent files indexer query."""
    try:
        pythoncom.CoInitialize()
        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.Open("Provider=Search.CollatorDSO;Extended Properties='Application=Windows';")
        rs = win32com.client.Dispatch("ADODB.Recordset")
        
        where_clauses = ["System.Kind <> 'folder'"]
        
        # File type (extension) filtering
        if file_types:
            ext_clauses = [f"System.FileExtension = '{ext.lower()}'" for ext in file_types]
            where_clauses.append(f"({' OR '.join(ext_clauses)})")
            
        query = (
            "SELECT TOP 15 System.ItemNameDisplay, System.ItemPathDisplay, System.DateModified "
            "FROM SystemIndex "
            f"WHERE {' AND '.join(where_clauses)} "
            "ORDER BY System.DateModified DESC"
        )
        
        try:
            rs.Open(query, conn)
            results = []
            while not rs.EOF:
                name = rs.Fields.Item("System.ItemNameDisplay").Value
                path = rs.Fields.Item("System.ItemPathDisplay").Value
                mtime = rs.Fields.Item("System.DateModified").Value
                
                dt_str = mtime.strftime("%d %b %Y, %I:%M %p") if hasattr(mtime, "strftime") else str(mtime)
                results.append(f"  {name}  —  {path}  ({dt_str})")
                rs.MoveNext()
                
            if not results:
                return "No recent files found in your indexed folders."
                
            return "Your most recently modified files:\n\n" + "\n".join(results)
            
        finally:
            if rs.State == 1: rs.Close()
            conn.Close()
            
    except Exception as exc:
        logger.error("Recent files indexer query failed: %s", exc)
        return f"Could not retrieve recent files: {exc}"
    finally:
        pythoncom.CoUninitialize()


async def _recent_downloads() -> str:
    downloads = Path.home() / "Downloads"
    if not downloads.exists():
        return "Could not find your Downloads folder."

    files = [(f.stat().st_mtime, f) for f in downloads.iterdir() if f.is_file()]
    if not files:
        return "Your Downloads folder is empty."

    files.sort(reverse=True)
    lines = ["Your most recent downloads:\n"]
    for mtime, path in files[:_MAX_RESULTS]:
        dt = datetime.fromtimestamp(mtime).strftime("%d %b %Y, %I:%M %p")
        lines.append(f"  {path.name}  ({dt})")
    return "\n".join(lines)


def _resolve_time_hint(hint: str) -> datetime | None:
    delta = _TIME_HINTS.get(hint)
    if delta is None:
        return None
    return datetime.now() - delta
