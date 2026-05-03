"""
graph.py — LangGraph agent graph for AutoOS.

Multi-step loop architecture:

  planner → router → executor → evaluator → {
    "continue" → planner (loop back)
    "end"      → memory_consolidator → END
  }

The evaluator checks if the original user task is fully complete.
If remaining sub-tasks exist, it loops back to the planner with
a new `remaining_task`. A hard safety cap (MAX_AGENT_STEPS) prevents
infinite loops.
"""
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes.planner import planner
from agent.nodes.router import router
from agent.nodes.executor import browser_executor, os_executor, reasoning_executor
from agent.nodes.evaluator import evaluator, should_continue
from agent.nodes.memory import memory_consolidator


def create_graph():
    workflow = StateGraph(AgentState)

    # ── Add all nodes ────────────────────────────────────────────────────────
    workflow.add_node("planner", planner)
    workflow.add_node("browser_executor", browser_executor)
    workflow.add_node("os_executor", os_executor)
    workflow.add_node("reasoning_executor", reasoning_executor)
    workflow.add_node("evaluator", evaluator)
    workflow.add_node("memory_consolidator", memory_consolidator)

    # ── Entry point ──────────────────────────────────────────────────────────
    workflow.set_entry_point("planner")

    # ── Planner → Router → Executor ──────────────────────────────────────────
    workflow.add_conditional_edges(
        "planner",
        router,
        {
            "browser_executor": "browser_executor",
            "os_executor": "os_executor",
            "reasoning_executor": "reasoning_executor",
            "end": "memory_consolidator",
        }
    )

    # ── Executors → Evaluator ────────────────────────────────────────────────
    workflow.add_edge("browser_executor", "evaluator")
    workflow.add_edge("os_executor", "evaluator")
    workflow.add_edge("reasoning_executor", "evaluator")

    # ── Evaluator → Loop or Finish ───────────────────────────────────────────
    workflow.add_conditional_edges(
        "evaluator",
        should_continue,
        {
            "continue": "planner",           # Loop back for next sub-task
            "end": "memory_consolidator",     # All done — consolidate & finish
        }
    )

    # ── Memory → END ─────────────────────────────────────────────────────────
    workflow.add_edge("memory_consolidator", END)

    return workflow.compile()


# Singleton instance
app_graph = create_graph()
