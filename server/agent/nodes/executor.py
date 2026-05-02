from typing import Any
from server.agent.state import AgentState
from server.agent.tools.browser_tool import run_browser_task

async def browser_executor(state: AgentState) -> dict[str, Any]:
    """
    Executes the browser-based task.
    """
    task = state.get("task", "")
    result = await run_browser_task(task)
    return {
        "result": result,
        "messages": [{"role": "assistant", "content": f"Browser Task Result: {result}"}]
    }

async def os_executor(state: AgentState) -> dict[str, Any]:
    """
    Placeholder for OS-based task execution (Agent-S).
    """
    return {
        "result": "OS Automation (Agent-S) not fully implemented yet.",
        "messages": [{"role": "assistant", "content": "OS Request detected. Agent-S integration is pending."}]
    }
