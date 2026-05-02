"""
LangGraph Agent Graph — the agentic loop.

Flow:
  START → gateway_agent → should_continue? → tool_executor → gateway_agent → ... → END

The gateway_agent calls Gemini with tools. If Gemini wants to use a tool,
the router sends it to tool_executor. After execution, it loops back to
gateway_agent for the next decision. This continues until the agent is done
or max iterations are reached.
"""

from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes.planner import gateway_agent
from agent.nodes.executor import tool_executor
from agent.nodes.router import should_continue


def create_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("gateway_agent", gateway_agent)
    workflow.add_node("tool_executor", tool_executor)

    # Entry point
    workflow.set_entry_point("gateway_agent")

    # After gateway_agent, decide: call tool, loop back, or end
    workflow.add_conditional_edges(
        "gateway_agent",
        should_continue,
        {
            "tool_executor": "tool_executor",
            "gateway_agent": "gateway_agent",
            "end": END,
        }
    )

    # After tool_executor, always go back to gateway_agent
    workflow.add_edge("tool_executor", "gateway_agent")

    return workflow.compile()


# Singleton instance
app_graph = create_graph()
