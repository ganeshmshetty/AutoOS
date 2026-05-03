"""
memory.py — Final node in the AutoOS agent graph.

Consolidates results, emits the final 'complete' event to the frontend,
and persists execution context to the local memory files.
"""
import os
from datetime import datetime
from agent.state import AgentState
from agent.bus import emit_event
from langchain_core.runnables import RunnableConfig

MEMORY_FILE = "server/knowledge/MEMORY.md"
HABITS_FILE = "server/knowledge/HABITS.md"


async def memory_consolidator(state: AgentState, config: RunnableConfig):
    """
    Final node: consolidates multi-step results and emits 'complete'.
    """
    task = state.get("task", "")
    step_results = state.get("step_results", [])
    result = state.get("result", "")
    steps_taken = state.get("steps_taken", 0)

    # Build a combined summary from all steps
    if len(step_results) > 1:
        summary_lines = [f"Completed in {steps_taken} steps:"]
        for i, r in enumerate(step_results):
            summary_lines.append(f"  {i+1}. {r}")
        final_summary = "\n".join(summary_lines)
    else:
        final_summary = result or (step_results[0] if step_results else "Task completed.")

    # Emit the final 'complete' event to the frontend
    await emit_event(config, {"type": "complete", "summary": final_summary})

    # ── Persist to local memory files ─────────────────────────────────────
    category = state.get("sub_category", "unknown")

    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                content = f.read()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            short_result = final_summary[:80].replace("\n", " ")
            new_entry = f"\n- [{timestamp}] {task} -> {short_result}..."

            if "## Recent Tasks" in content:
                updated = content.replace("## Recent Tasks", f"## Recent Tasks{new_entry}")
                with open(MEMORY_FILE, "w") as f:
                    f.write(updated)
        except Exception:
            pass  # Non-critical

    if os.path.exists(HABITS_FILE):
        keywords = ["whatsapp", "calc", "browser", "downloads"]
        found = [k for k in keywords if k in task.lower()]
        if found:
            try:
                with open(HABITS_FILE, "a") as f:
                    f.write(f"\n- Observed usage of {', '.join(found)} at {datetime.now()}")
            except Exception:
                pass

    return {
        "result": final_summary,
        "messages": [{
            "role": "assistant",
            "content": final_summary,
        }],
    }
