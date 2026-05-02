from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes.planner import planner
from agent.nodes.router import router
from agent.nodes.executor import browser_executor, os_executor

def create_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("planner", planner)
    workflow.add_node("browser_executor", browser_executor)
    workflow.add_node("os_executor", os_executor)

    # Set Entry Point
    workflow.set_entry_point("planner")

    # Add Conditional Edges (The Gateway)
    workflow.add_conditional_edges(
        "planner",
        router,
        {
            "browser_executor": "browser_executor",
            "os_executor": "os_executor",
            "end": END
        }
    )

    # Transitions to END
    workflow.add_edge("browser_executor", END)
    workflow.add_edge("os_executor", END)

    return workflow.compile()

# Singleton instance
app_graph = create_graph()
