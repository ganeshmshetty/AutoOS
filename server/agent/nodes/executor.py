from typing import Any
import asyncio
from langchain_core.runnables import RunnableConfig
from server.agent.state import AgentState
from server.agent.tools.browser_tool import run_browser_task
from server.agent.bus import emit_event

async def browser_executor(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Executes the browser-based task.
    """
    task = state.get("task", "")
    await emit_event(config, {"type": "step_start", "description": f"Starting browser task: {task}"})
    
    result = await run_browser_task(
        task,
        headless=state.get("headless"),
        input_values=state.get("input_values"),
        max_steps=state.get("max_steps"),
    )
    
    await emit_event(config, {"type": "step_done", "description": f"Completed browser task"})
    await emit_event(config, {"type": "complete", "summary": result})
    
    return {
        "result": result,
        "messages": [{"role": "assistant", "content": f"Browser Task Result: {result}"}]
    }

async def os_executor(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Placeholder for OS-based task execution (Agent-S).
    """
    task = state.get("task", "")
    await emit_event(config, {"type": "step_start", "description": f"Starting OS task: {task}"})
    
    # Simple PyAutoGUI demo
    import pyautogui
    pyautogui.press('win')
    await asyncio.sleep(1)
    pyautogui.typewrite('Notepad')
    await asyncio.sleep(1)
    pyautogui.press('enter')
    
    result = "Launched Notepad as a demo of OS control."
    
    await emit_event(config, {"type": "step_done", "description": f"Completed OS task"})
    await emit_event(config, {"type": "complete", "summary": result})
    
    return {
        "result": result,
        "messages": [{"role": "assistant", "content": "OS Request detected. Demo action performed."}]
    }
