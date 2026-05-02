"""
Tool Executor Node — dispatches tool calls to the appropriate tool function
and returns the result back into the conversation.
"""

import json
import logging
from typing import Any

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig

from agent.state import AgentState
from agent.bus import emit_event

logger = logging.getLogger("AutoOS.tool_executor")


async def tool_executor(state: AgentState, config: RunnableConfig) -> dict:
    """
    Executes the most recent pending tool call and returns the result.
    """
    tool_history = list(state.get("tool_history", []))
    messages = list(state.get("messages", []))

    if not tool_history:
        logger.warning("Tool executor called with no pending tools")
        return {"messages": messages, "done": True}

    # Find the last pending tool call
    pending = None
    for th in reversed(tool_history):
        if th.get("status") == "pending":
            pending = th
            break

    if not pending:
        logger.warning("No pending tool calls found")
        return {"messages": messages, "done": True}

    tool_name = pending["tool"]
    tool_args = pending["args"]
    tool_id = pending.get("id", "unknown")

    logger.info(f"Executing tool: {tool_name}({json.dumps(tool_args)[:200]})")

    await emit_event(config, {
        "type": "step_start",
        "description": f"Running {tool_name}...",
        "tool": tool_name,
    })

    # Dispatch to the appropriate tool function
    try:
        result = await _dispatch_tool(tool_name, tool_args, config=config)
        result_str = json.dumps(result, indent=2, default=str) if isinstance(result, dict) else str(result)

        # Truncate very long results
        if len(result_str) > 3000:
            result_str = result_str[:3000] + "\n... (truncated)"

        logger.info(f"Tool result ({tool_name}): {result_str[:200]}")

        await emit_event(config, {
            "type": "tool_result",
            "tool": tool_name,
            "result": result_str[:500],  # Send shorter version to frontend
            "success": result.get("success", True) if isinstance(result, dict) else True,
        })

        # Mark the tool as completed in history
        for th in tool_history:
            if th.get("id") == tool_id and th.get("status") == "pending":
                th["status"] = "completed"
                th["result"] = result_str[:1000]
                break

        # Add the tool result as a ToolMessage to the conversation
        tool_message = ToolMessage(
            content=result_str,
            tool_call_id=tool_id,
        )

        return {
            "messages": messages + [tool_message],
            "tool_history": tool_history,
            "done": False,  # Continue the loop — agent needs to process the result
        }

    except Exception as e:
        error_msg = f"Tool execution failed: {str(e)}"
        logger.error(error_msg, exc_info=True)

        await emit_event(config, {
            "type": "step_error",
            "error": error_msg,
            "tool": tool_name,
        })

        # Mark failed
        for th in tool_history:
            if th.get("id") == tool_id and th.get("status") == "pending":
                th["status"] = "failed"
                th["result"] = error_msg
                break

        tool_message = ToolMessage(
            content=f"Error: {error_msg}",
            tool_call_id=tool_id,
        )

        return {
            "messages": messages + [tool_message],
            "tool_history": tool_history,
            "done": False,  # Let the agent decide what to do with the error
        }


async def _dispatch_tool(tool_name: str, args: dict, config: dict | None = None) -> Any:
    """Route tool calls to the appropriate implementation."""

    if tool_name == "run_terminal_command":
        from agent.tools.terminal_tool import run_terminal_command
        return await run_terminal_command(
            command=args.get("command", ""),
            working_directory=args.get("working_directory"),
            timeout=args.get("timeout", 30),
        )

    elif tool_name == "open_application":
        from agent.tools.desktop_tool import open_application
        return await open_application(app_name=args.get("app_name", ""))

    elif tool_name == "get_system_info":
        from agent.tools.desktop_tool import get_system_info
        return await get_system_info()

    elif tool_name == "list_directory":
        from agent.tools.desktop_tool import list_directory
        return await list_directory(path=args.get("path", "~"))

    elif tool_name == "read_file":
        from agent.tools.desktop_tool import read_file
        return await read_file(
            path=args.get("path", ""),
            max_lines=args.get("max_lines", 100),
        )

    elif tool_name == "write_file":
        from agent.tools.desktop_tool import write_file
        return await write_file(
            path=args.get("path", ""),
            content=args.get("content", ""),
        )

    elif tool_name == "search_files":
        from agent.tools.desktop_tool import search_files
        return await search_files(
            query=args.get("query", ""),
            search_path=args.get("search_path", "~"),
            file_type=args.get("file_type"),
        )

    elif tool_name == "get_clipboard":
        from agent.tools.desktop_tool import get_clipboard
        return await get_clipboard()

    elif tool_name == "set_clipboard":
        from agent.tools.desktop_tool import set_clipboard
        return await set_clipboard(text=args.get("text", ""))

    elif tool_name == "send_notification":
        from agent.tools.desktop_tool import send_notification
        return await send_notification(
            title=args.get("title", "AutoOS"),
            message=args.get("message", ""),
        )

    elif tool_name == "open_url":
        from agent.tools.desktop_tool import open_url
        return await open_url(url=args.get("url", ""))

    elif tool_name == "browse_web":
        from agent.tools.browser_tool import run_browser_task

        # Emit browser_start to trigger the live popup in the frontend
        if config:
            await emit_event(config, {
                "type": "browser_start",
                "task": args.get("task", ""),
            })

        # Create a step callback that streams steps to the frontend
        step_count = 0

        async def on_browser_step(agent):
            nonlocal step_count
            step_count += 1
            if not config:
                return

            memory = ""
            actions = []
            try:
                # The callback receives the agent instance. We can inspect its state/history.
                # agent.state.last_model_output contains the current action
                mo = getattr(agent.state, "last_model_output", None)
                if not mo and hasattr(agent, "history") and agent.history.history:
                    # fallback to history if state isn't populated
                    mo = agent.history.history[-1].model_output
                
                if mo:
                    if hasattr(mo, "current_state") and mo.current_state:
                        memory = getattr(mo.current_state, "memory", "") or ""
                    
                    if hasattr(mo, "action") and mo.action:
                        for act in (mo.action if isinstance(mo.action, list) else [mo.action]):
                            try:
                                act_dict = None
                                if hasattr(act, "model_dump"):
                                    act_dict = act.model_dump(exclude_unset=True, exclude_none=True)
                                elif isinstance(act, dict):
                                    act_dict = act
                                
                                if act_dict:
                                    for k, v in act_dict.items():
                                        if v is not None:
                                            if isinstance(v, dict) and "text" in v:
                                                actions.append(f"{k} '{v['text']}'")
                                            elif isinstance(v, dict) and "index" in v:
                                                actions.append(f"{k} [{v['index']}]")
                                            else:
                                                actions.append(str(k))
                                else:
                                    actions.append(str(act)[:100])
                            except Exception:
                                actions.append(str(act)[:100])
            except Exception as e:
                import logging
                logging.getLogger("AutoOS").warning(f"Error extracting browser step data: {e}")

            await emit_event(config, {
                "type": "browser_step",
                "step": step_count,
                "memory": memory[:300] if memory else "",
                "actions": actions[:5],
            })

        result_text = await run_browser_task(
            task=args.get("task", ""),
            on_step=on_browser_step,
        )

        # Emit browser_end
        if config:
            await emit_event(config, {
                "type": "browser_end",
            })

        return {"success": True, "result": result_text}

    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
