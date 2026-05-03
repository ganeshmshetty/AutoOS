"""
executor.py — Execution nodes for the AutoOS LangGraph agent.

Contains three executor nodes:
  • browser_executor — delegates to browser_use agent
  • os_executor     — dispatches to modular handlers via desktop_tool
  • reasoning_executor — uses LLM for knowledge/math questions

The OS executor now uses the planner's structured output (sub_category,
entities, action_params) to dispatch to the correct module dynamically,
instead of re-parsing the raw task string with regex.
"""
from typing import Any
import asyncio
import logging

from langchain_core.runnables import RunnableConfig
from agent.state import AgentState
from agent.tools.browser_tool import run_browser_task
from agent.tools.desktop_tool import run_os_task
from agent.bus import emit_event

logger = logging.getLogger("AutoOS.executor")


# ─────────────────────────────────────────────────────────────────────────────
# BROWSER EXECUTOR
# ─────────────────────────────────────────────────────────────────────────────

async def browser_executor(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    task = state.get("task", "")

    await emit_event(config, {
        "type": "step_start",
        "description": f"Starting browser task: {task}"
    })

    try:
        result = await asyncio.wait_for(
            run_browser_task(
                task,
                headless=state.get("headless"),
                input_values=state.get("input_values"),
                max_steps=state.get("max_steps"),
            ),
            timeout=120.0
        )
    except asyncio.TimeoutError:
        result = "Browser task timed out after 2 minutes. Please try again."
    except Exception as e:
        result = f"Browser task failed: {str(e)}"

    await emit_event(config, {"type": "step_done", "description": "Completed browser task"})

    # Detect current platform for context persistence
    new_ctx = {}
    if "spotify.com" in str(result).lower() or "spotify" in task.lower():
        new_ctx["last_url"] = "https://open.spotify.com"
        new_ctx["last_app"] = "spotify"
    elif "youtube.com" in str(result).lower() or "youtube" in task.lower():
        new_ctx["last_url"] = "https://www.youtube.com"
        new_ctx["last_app"] = "youtube"

    return {
        "result": result,
        "step_results": [result],
        "messages": [{"role": "assistant", "content": f"Browser Task Result: {result}"}],
        "context": new_ctx
    }


# ─────────────────────────────────────────────────────────────────────────────
# OS EXECUTOR — Dynamic dispatch using planner's structured output
# ─────────────────────────────────────────────────────────────────────────────

# Status messages for each sub_category (human-friendly)
_STATUS_MAP = {
    "app_launch":   "Launching the app for you...",
    "app_control":  "Interacting with the app...",
    "file_ops":     "Working with your files...",
    "hardware":     "Checking your hardware...",
    "settings":     "Adjusting your settings...",
    "process_mgmt": "Managing your processes...",
    "security":     "Running a security check...",
    "diagnostics":  "Running diagnostics...",
    "vision":       "Analyzing what's on screen...",
}


async def os_executor(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Executes OS tasks by dispatching to modular handlers.
    
    Uses the planner's structured output:
      - sub_category → which module to call
      - entities     → key nouns extracted from the task
      - action_params→ structured parameters for the module
    
    This makes the executor truly dynamic — adding a new capability
    only requires adding a new module and a new sub_category in the planner.
    """
    task = state.get("task", "")
    sub_category = state.get("sub_category", "unknown")
    entities = state.get("entities", [])
    action_params = state.get("action_params", {})

    # Human-friendly status
    status_msg = _STATUS_MAP.get(sub_category, f"Working on: {task}")

    await emit_event(config, {
        "type": "classification",
        "category": "os",
        "sub_category": sub_category,
        "description": status_msg,
    })
    await emit_event(config, {
        "type": "step_start",
        "description": status_msg,
    })

    try:
        # Dispatch to the correct module using the planner's structured output
        result = await run_os_task(
            task=task,
            sub_category=sub_category,
            entities=entities,
            action_params=action_params,
        )
    except Exception as e:
        logger.error("OS executor error: %s", e, exc_info=True)
        result = f"Something went wrong: {str(e)}"

    await emit_event(config, {"type": "step_done", "description": f"Done! {result}"})

    # Build context updates from entities for chaining
    new_ctx = {}
    if entities:
        new_ctx["last_entities"] = entities
    if sub_category == "app_launch" and entities:
        new_ctx["last_app"] = entities[0]

    return {
        "result": result,
        "step_results": [result],
        "messages": [{"role": "assistant", "content": result}],
        "context": new_ctx,
    }


# ─────────────────────────────────────────────────────────────────────────────
# REASONING EXECUTOR
# ─────────────────────────────────────────────────────────────────────────────

async def reasoning_executor(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    task = state.get("task", "")

    await emit_event(config, {
        "type": "step_start",
        "description": f"Thinking about: {task}"
    })

    try:
        from agent.llm_factory import get_llm
        llm = get_llm(temperature=0.7)

        ctx = state.get("context", {})

        prompt = f"""You are the Reasoning Engine of AutoOS. 
        Current Task: {task}
        Context: {ctx}
        
        Provide a clear, helpful, and accurate response. If this is a math or physics problem, show your work briefly.
        Keep it friendly and concise."""

        response = await llm.ainvoke(prompt)
        result = response.content
    except Exception as e:
        result = f"Reasoning failed: {str(e)}"

    await emit_event(config, {"type": "step_done", "description": "Finished thinking."})

    return {
        "result": result,
        "step_results": [result],
        "messages": [{"role": "assistant", "content": result}]
    }


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY: Process killer (used by main.py /system/processes/kill endpoint)
# ─────────────────────────────────────────────────────────────────────────────

def kill_process(name_or_pid: str) -> str:
    """Safely terminates a process using psutil."""
    import psutil
    count = 0
    try:
        if name_or_pid.isdigit():
            p = psutil.Process(int(name_or_pid))
            p.terminate()
            return f"Terminated process with PID {name_or_pid}."

        for proc in psutil.process_iter(['name']):
            if name_or_pid.lower() in proc.info['name'].lower():
                proc.terminate()
                count += 1

        if count > 0:
            return f"Successfully closed {count} instances of '{name_or_pid}'."
        return f"No active process found named '{name_or_pid}'."
    except Exception as e:
        return f"Failed to kill process: {e}"
