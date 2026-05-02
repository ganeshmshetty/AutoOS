"""
executor.py — Browser and OS executor nodes for AutoOS LangGraph.
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.runnables import RunnableConfig

from server.agent.bus import emit_event
from server.agent.state import AgentState
from server.agent.tools.browser_tool import run_browser_task
from server.agent.tools.desktop_tool import run_os_task

logger = logging.getLogger("AutoOS.executor")


async def browser_executor(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Executes a browser-based task using browser-use.
    Refines the task description using action_params for better accuracy.
    """
    task = state.get("task", "")
    plan = state.get("plain_english_plan", task)
    action_params = state.get("action_params", {})
    sub_category = state.get("sub_category", "web_search")

    # Build a more specific task string for browser-use using action_params
    refined_task = _refine_browser_task(task, sub_category, action_params)

    await emit_event(config, {"type": "step_start", "description": plan})

    result = await run_browser_task(
        refined_task,
        headless=state.get("headless"),
        input_values=state.get("input_values"),
        max_steps=state.get("max_steps"),
    )

    await emit_event(config, {"type": "step_done", "description": "Browser task completed"})
    await emit_event(config, {"type": "complete", "summary": result})

    return {
        "result": result,
        "messages": [{"role": "assistant", "content": f"Browser Result: {result}"}],
    }


def _refine_browser_task(task: str, sub_category: str, params: dict) -> str:
    """
    Construct a more specific task string for the browser-use agent
    using the structured params from the planner.
    """
    match sub_category:
        case "media_playback":
            platform = params.get("platform", "")
            query = params.get("query", "")
            content_type = params.get("content_type", "")
            if platform and query:
                return f"Go to {platform} and play {content_type + ' ' if content_type else ''}{query}"
        case "web_search":
            query = params.get("query", "")
            if query:
                return f"Search the web for: {query}"
        case "gov_portal":
            portal = params.get("portal", "")
            action = params.get("action", "open")
            if portal:
                return f"{action.capitalize()} {portal}"
        case "web_form":
            site = params.get("site", "")
            action = params.get("action", "")
            if site and action:
                return f"Go to {site} and {action}"
    return task  # fallback to original task


async def os_executor(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Executes an OS task by dispatching to the correct module.
    Passes sub_category, entities, and action_params — never parses raw task text here.
    """
    task = state.get("task", "")
    sub_category = state.get("sub_category", "unknown")
    entities = state.get("entities", [])
    action_params = state.get("action_params", {})
    plan = state.get("plain_english_plan", task)

    logger.info("OS executor: sub=%s params=%s", sub_category, action_params)
    await emit_event(config, {"type": "step_start", "description": plan})

    result = await run_os_task(
        task,
        sub_category=sub_category,
        entities=entities,
        action_params=action_params,
    )

    await emit_event(config, {"type": "step_done", "description": "Task completed"})
    await emit_event(config, {"type": "complete", "summary": result})

    return {
        "result": result,
        "messages": [{"role": "assistant", "content": f"Result: {result}"}],
    }
