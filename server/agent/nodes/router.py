"""
Router — conditional edge function for the agentic loop.
Determines if the agent should continue (call more tools) or stop.
"""

import logging
from agent.state import AgentState

logger = logging.getLogger("AutoOS.router")

MAX_ITERATIONS = 15


def should_continue(state: AgentState) -> str:
    """
    Determines the next step in the graph:
    - "tool_executor" if the agent wants to call a tool
    - "end" if the agent is done or max iterations reached
    """
    done = state.get("done", False)
    iteration = state.get("iteration", 0)

    if done:
        logger.info(f"Agent is done after {iteration} iterations")
        return "end"

    if iteration >= MAX_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, forcing stop")
        return "end"

    # Check if there's a pending tool call
    tool_history = state.get("tool_history", [])
    has_pending = any(th.get("status") == "pending" for th in tool_history)

    if has_pending:
        logger.info(f"Routing to tool_executor (iteration {iteration})")
        return "tool_executor"

    # No pending tools and not done — go back to agent for another round
    logger.info(f"Routing back to gateway_agent (iteration {iteration})")
    return "gateway_agent"
