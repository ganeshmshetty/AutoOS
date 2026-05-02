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
    keywords: list[str] = action_params.get("keywords") or entities or []
    file_types: list[str] = action_params.get("file_types") or []
    time_hint: str = action_params.get("time_hint", "any")
    action: str = action_params.get("action", "search")
    folder: str | None = action_params.get("folder")

    # Determine the requested action (default is search)
    action: str = action_params.get("action", "search")
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
        # Fallback: search across user roots
        for root in _USER_ROOTS:
            try:
                for f in root.rglob(target_name):
                    os.startfile(str(f))
                    return f"Opened {target_name} from {root}."
            except Exception:
                continue
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


async def _search_files(keywords: list[str], file_types: list[str], time_hint: str) -> str:
    kw_lower = [k.lower() for k in keywords]
    allowed_exts = set(file_types)
    cutoff_dt = _resolve_time_hint(time_hint)
    results: list[tuple[datetime, Path]] = []

    for root in _USER_ROOTS:
        if not root.exists():
            continue
        try:
            for f in root.rglob("*"):
                if not f.is_file():
                    continue
                if allowed_exts and f.suffix.lower() not in allowed_exts:
                    continue
                name_lower = f.name.lower()
                if not any(kw in name_lower for kw in kw_lower):
                    continue
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    if cutoff_dt and mtime < cutoff_dt:
                        continue
                    results.append((mtime, f))
                except OSError:
                    continue
        except PermissionError:
            continue

    if not results:
        return f"No files matching '{', '.join(keywords)}' found in your common folders."

    results.sort(key=lambda x: x[0], reverse=True)
    lines = [f"Found {len(results)} file(s) matching your request:\n"]
    for mtime, path in results[:_MAX_RESULTS]:
        lines.append(f"  {path.name}  —  {path.parent}  ({mtime.strftime('%d %b %Y')})")
    return "\n".join(lines)


async def _recent_files(entities: list[str], file_types: list[str]) -> str:
    allowed_exts: set[str] = set(file_types)
    if not allowed_exts:
        # Infer from entity names
        for entity in entities:
            for key, exts in _EXT_MAP.items():
                if key in entity.lower():
                    allowed_exts.update(exts)

    results: list[tuple[datetime, Path]] = []
    for root in _USER_ROOTS:
        if not root.exists():
            continue
        try:
            for f in root.rglob("*"):
                if not f.is_file():
                    continue
                if allowed_exts and f.suffix.lower() not in allowed_exts:
                    continue
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    results.append((mtime, f))
                except OSError:
                    continue
        except PermissionError:
            continue

    if not results:
        return "No recent files found in your common folders."

    results.sort(key=lambda x: x[0], reverse=True)
    lines = ["Your most recently modified files:\n"]
    for mtime, path in results[:_MAX_RESULTS]:
        lines.append(
            f"  {path.name}  —  {path.parent}  "
            f"(last edited {mtime.strftime('%d %b %Y, %I:%M %p')})"
        )
    return "\n".join(lines)


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
