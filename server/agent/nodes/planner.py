"""
Gateway Agent Node — the brain of the agentic loop.

This node calls Gemini with function declarations for all available tools.
Gemini decides whether to call a tool or return a final answer.
"""

import os
import json
import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from agent.state import AgentState
from agent.bus import emit_event

logger = logging.getLogger("AutoOS.gateway_agent")

# ─── Tool Definitions (Gemini Function Declarations) ────────────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "run_terminal_command",
            "description": "Execute a shell command in the terminal. Use this for any task that can be done via command line: checking system info, installing packages, running scripts, git operations, file manipulation, etc. Returns stdout, stderr, and exit code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute. Examples: 'ls -la', 'date', 'df -h', 'python3 --version'"
                    },
                    "working_directory": {
                        "type": "string",
                        "description": "Optional working directory. Defaults to home directory. Use ~ for home."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds. Default 30."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open a desktop application by name. Works on macOS (uses 'open -a'). Examples: 'Safari', 'Chrome', 'Terminal', 'Finder', 'Calculator', 'Visual Studio Code', 'Slack'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "The name of the application to open."
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get comprehensive system information including CPU usage, memory, disk space, battery status, platform details.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List the contents of a directory. Shows files and folders with sizes and modification dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory. Use ~ for home directory. Examples: '~', '~/Downloads', '~/Documents'"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file. Limited to 100 lines and 1MB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read."
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum number of lines to read. Default 100."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates parent directories if needed. Overwrites existing content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path where the file should be written."
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content to write to the file."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files by name pattern within a directory (recursive). Returns up to 20 results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term to match in file names."
                    },
                    "search_path": {
                        "type": "string",
                        "description": "Directory to search in. Defaults to ~. Examples: '~', '~/Documents'"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "Optional file extension filter. Examples: 'pdf', 'py', 'txt'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Read the current clipboard contents (what the user last copied).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "Copy text to the clipboard so the user can paste it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to copy to the clipboard."
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_notification",
            "description": "Send a desktop notification to the user with a title and message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Notification title."
                    },
                    "message": {
                        "type": "string",
                        "description": "Notification body text."
                    }
                },
                "required": ["title", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Passively open a URL in the default browser and leave it — no further interaction. Use ONLY when the user literally just wants to open/view a page and nothing else (e.g. 'open google.com'). Do NOT use this before browse_web — browse_web already opens the browser on its own.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to open. Must include protocol (https://)."
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browse_web",
            "description": "Launch a full AI-controlled browser agent to perform ANY multi-step web task: searching, clicking, form filling, playing media, logging in, extracting data, navigating across pages. The agent opens the browser by itself — never call open_url before this. Use browse_web any time the task requires interacting with a website beyond just viewing it. Provide a rich, detailed task description including the target site and exact actions expected.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Detailed description of what to do in the browser. Include the website name, exactly what to search/click/fill, and the desired outcome. Example: 'Go to youtube.com, search for a popular song, click the first video result and let it play.'"
                    }
                },
                "required": ["task"]
            }
        }
    },
]

# ─── System Prompt ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are AutoOS, an intelligent desktop automation assistant running on macOS. You help users accomplish tasks using the tools available to you.

CAPABILITIES:
- Terminal: run any shell/CLI command
- Open App: launch macOS applications by name
- File tools: read, write, list, search files
- System Info: CPU, memory, disk, battery status
- Clipboard: read or write clipboard
- Notifications: send desktop alerts
- open_url: passively open a URL for viewing only
- browse_web: AI-controlled browser for ANY interactive web task

CRITICAL TOOL SELECTION RULES:
1. If the user wants to DO something on a website (search, click, play, login, fill forms, extract data) → use browse_web ONLY. Never call open_url before browse_web — browse_web opens the browser itself.
2. Use open_url ONLY if the user literally just wants to open a page with no further action (e.g. "open google.com").
3. For tasks like "open YouTube and play a song", "search Google for X", "book a flight" → go straight to browse_web with a rich task description.
4. One tool call at a time. Wait for results before calling the next tool.
5. Keep responses short and plain. Avoid technical jargon unless the user is clearly technical.
6. After all tools complete, give one clean summary sentence of what was accomplished.
7. If a tool fails, try a different approach rather than repeating the same call.
8. Never run destructive terminal commands (rm -rf, format, etc.) without explicit confirmation.

FORMATTING:
- Do NOT narrate every step verbosely — be brief before calling a tool.
- After getting a tool result, synthesize it into plain English for the user.
- Final summary should be 1-2 sentences max.
"""


def _get_llm():
    """Create the Gemini LLM instance."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        keys = os.getenv("LLM_API_KEYS", "")
        if keys:
            api_key = keys.split(",")[0].strip()

    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is required. Set it in server/.env")

    model_name = os.getenv("LLM_MODEL", "gemini-2.0-flash")

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.1,
    )
    return llm


async def gateway_agent(state: AgentState, config: RunnableConfig) -> dict:
    """
    The core reasoning node. Calls Gemini with tool definitions.
    Returns either a tool call request or a final answer.
    """
    task = state.get("task", "")
    messages = list(state.get("messages", []))
    iteration = state.get("iteration", 0)
    execution_id = state.get("execution_id", "")

    logger.info(f"Gateway agent iteration {iteration}, messages: {len(messages)}")

    # First iteration: add the system prompt and user task
    if iteration == 0:
        if not task:
            return {
                "result": "No task provided.",
                "done": True,
                "messages": [AIMessage(content="No task provided.")],
            }

        await emit_event(config, {
            "type": "thinking",
            "message": "Understanding your request..."
        })

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=task),
        ]

    # Build the LLM with tools
    llm = _get_llm()

    # Convert our tool definitions to langchain tool format
    from langchain_core.tools import tool as langchain_tool

    # Use bind_tools with the raw function schema
    tools_for_binding = []
    for td in TOOL_DEFINITIONS:
        func_def = td["function"]
        tools_for_binding.append({
            "name": func_def["name"],
            "description": func_def["description"],
            "parameters": func_def.get("parameters", {"type": "object", "properties": {}}),
        })

    llm_with_tools = llm.bind_tools(tools_for_binding)

    # Call Gemini
    try:
        response = await llm_with_tools.ainvoke(messages)
    except Exception as e:
        logger.error(f"LLM call failed: {e}", exc_info=True)
        error_msg = f"I encountered an error: {str(e)}"
        await emit_event(config, {"type": "step_error", "error": error_msg})
        return {
            "result": error_msg,
            "done": True,
            "messages": messages + [AIMessage(content=error_msg)],
            "iteration": iteration + 1,
        }

    # Check if the response has tool calls
    tool_calls = response.tool_calls if hasattr(response, "tool_calls") else []

    if tool_calls and len(tool_calls) > 0:
        # The LLM wants to call a tool
        tool_call = tool_calls[0]  # Process one tool at a time for clarity
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        tool_id = tool_call.get("id", f"call_{iteration}")

        logger.info(f"Tool call: {tool_name}({json.dumps(tool_args)[:200]})")

        await emit_event(config, {
            "type": "tool_call",
            "tool": tool_name,
            "args": tool_args,
        })

        # Add the AI message with tool call to history
        updated_messages = messages + [response]

        return {
            "messages": updated_messages,
            "iteration": iteration + 1,
            "done": False,
            "result": "",
            # Store the pending tool call info in tool_history for the executor
            "tool_history": state.get("tool_history", []) + [{
                "tool": tool_name,
                "args": tool_args,
                "id": tool_id,
                "status": "pending",
            }],
        }
    else:
        # The LLM returned a final text answer
        # response.content can be a string OR a list of parts like
        # [{'type': 'text', 'text': '...', 'extras': {...}}]
        raw_content = response.content if hasattr(response, "content") else str(response)
        if isinstance(raw_content, list):
            # Extract text from content parts
            parts = []
            for part in raw_content:
                if isinstance(part, dict) and part.get("text"):
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            final_text = " ".join(parts) if parts else str(raw_content)
        else:
            final_text = str(raw_content) if raw_content else "Task completed."

        logger.info(f"Final answer: {final_text[:200]}")

        await emit_event(config, {
            "type": "complete",
            "summary": final_text,
        })

        return {
            "messages": messages + [response],
            "iteration": iteration + 1,
            "done": True,
            "result": final_text,
        }
