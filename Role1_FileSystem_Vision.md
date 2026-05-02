# Role 1: File System & System Vision

## Objective
Implement smart file management and visual system diagnostics using Python 3.12 and the Agent-S framework.

## Tech Stack
- **Python 3.12**
- **Agent-S** (`gui-agents`)
- **System APIs**: `os`, `shutil`, `glob`

## Tasks & Requirements

### 1. Smart File Search
- **Functionality**: Create a script that searches for files by name, date, or type.
- **Agent-S Integration**: Use Agent-S to visually navigate Windows Explorer if direct script-based search fails or if the user asks "Where is my file?" in a way that requires visual confirmation.

### 2. Lost Download Finder
- **Functionality**: Automatically locate recently downloaded files in common folders (Downloads, Desktop, Chrome/Edge default paths).
- **Agent-S Integration**: Use Agent-S to open browser download history and visually identify the most recent downloads.

### 3. Storage Health & Cleanup
- **Functionality**: Monitor disk space and alert when storage is full.
- **Automation**: Build a "cleanup assistant" that clears temporary files, recycle bin, and cache.

### 4. "Visual Explainer" for System Errors
- **Functionality**: Capture the screen when an error occurs (or if a user is stuck on a BSOD/Blue Screen).
- **Agent-S Integration**: Use Agent-S's visual perception to "read" the error and explain it in plain, jargon-free English to the user.

## Rules
- **Zero Jargon**: All status reports and errors must be returned in plain language.
- **Headless First**: Build logic as standalone modules that can be triggered via a central API.
