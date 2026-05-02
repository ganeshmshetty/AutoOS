from typing import Annotated, TypedDict, List, Any
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for the AutoOS agentic gateway loop."""

    # The messages in the conversation (LangChain message format)
    messages: Annotated[list, add_messages]
    # The current task description from the user
    task: str
    # Execution ID for WebSocket event routing
    execution_id: str
    # Tool call history: list of {tool, args, result} dicts
    tool_history: List[dict]
    # Current loop iteration (safety counter)
    iteration: int
    # Final result text
    result: str
    # Whether the agent loop is finished
    done: bool
