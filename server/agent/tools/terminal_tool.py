"""
Terminal tool — executes shell commands safely with timeout and output capture.
"""

import asyncio
import logging
import platform
import os

logger = logging.getLogger("AutoOS.terminal")

# Commands that are too dangerous to run
BLOCKED_COMMANDS = {
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=", ":(){", "fork bomb",
    "sudo rm -rf", "format c:", "deltree",
}

MAX_OUTPUT_LENGTH = 4000  # Truncate output to avoid blowing up context


async def run_terminal_command(
    command: str,
    working_directory: str | None = None,
    timeout: int = 30,
) -> dict:
    """
    Execute a shell command and return structured output.

    Returns:
        dict with keys: exit_code, stdout, stderr, success
    """
    # Safety check
    cmd_lower = command.lower().strip()
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command blocked for safety: contains '{blocked}'",
                "success": False,
            }

    cwd = working_directory or os.path.expanduser("~")
    if not os.path.isdir(cwd):
        cwd = os.path.expanduser("~")

    logger.info(f"Executing command: {command} (cwd={cwd}, timeout={timeout}s)")

    try:
        # Use the system shell
        shell = "/bin/zsh" if platform.system() == "Darwin" else "/bin/bash"

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env={**os.environ},
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "success": False,
            }

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        # Truncate if too long
        if len(stdout) > MAX_OUTPUT_LENGTH:
            stdout = stdout[:MAX_OUTPUT_LENGTH] + "\n... (output truncated)"
        if len(stderr) > MAX_OUTPUT_LENGTH:
            stderr = stderr[:MAX_OUTPUT_LENGTH] + "\n... (output truncated)"

        exit_code = process.returncode or 0
        success = exit_code == 0

        logger.info(f"Command finished: exit_code={exit_code}, stdout_len={len(stdout)}")

        return {
            "exit_code": exit_code,
            "stdout": stdout.strip(),
            "stderr": stderr.strip(),
            "success": success,
        }

    except Exception as e:
        logger.error(f"Command execution failed: {e}", exc_info=True)
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
        }
