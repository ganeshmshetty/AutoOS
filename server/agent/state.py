from typing import Annotated, TypedDict, List
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # The messages in the conversation
    messages: Annotated[List[dict], add_messages]
    # The current task description
    task: str
    # The classification: "browser" or "os"
    next_action: str
    # The plan of steps
    plan: List[str]
    # Final result
    result: str
