"""
evaluator.py — Multi-step loop controller for AutoOS.

After each executor step, the evaluator decides:
  • "continue" → the original task has remaining sub-tasks, loop back to planner
  • "end"      → the task is fully complete, proceed to memory and finish

Uses a fast LLM call to check completeness. Has a hard safety cap
(MAX_AGENT_STEPS) to prevent infinite loops.
"""
from __future__ import annotations

import logging
from typing import Any, Literal

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from agent.bus import emit_event
from agent.llm_factory import get_llm, invoke_with_fallback
from agent.state import AgentState

logger = logging.getLogger("AutoOS.evaluator")

# Safety limit — never loop more than this many times
MAX_AGENT_STEPS = 5


# ── Structured output for the evaluator ───────────────────────────────────────

class EvalDecision(BaseModel):
    is_complete: bool = Field(
        description="True if the ORIGINAL user task has been fully accomplished."
    )
    remaining_task: str = Field(
        default="",
        description=(
            "If is_complete is False, describe what STILL NEEDS TO BE DONE "
            "as a new actionable instruction (max 30 words). "
            "If is_complete is True, leave this empty."
        ),
    )
    reasoning: str = Field(
        default="",
        description="One sentence explaining why the task is or isn't complete.",
    )


# ── Evaluator node ────────────────────────────────────────────────────────────

async def evaluator(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Checks if the original user task is fully complete after the latest
    executor step. If not, it sets `remaining_task` for the planner to
    pick up on the next loop iteration.
    """
    task = state.get("task", "")
    steps_taken = state.get("steps_taken", 0)
    step_results = state.get("step_results", [])
    latest_result = state.get("result", "")

    # ── Hard safety cap ───────────────────────────────────────────────────
    if steps_taken >= MAX_AGENT_STEPS:
        logger.warning(
            "Hit MAX_AGENT_STEPS (%d) for task: %s — forcing completion",
            MAX_AGENT_STEPS, task,
        )
        await emit_event(config, {
            "type": "step_info",
            "description": f"Reached max steps ({MAX_AGENT_STEPS}). Wrapping up.",
        })
        return {
            "remaining_task": "",
            "steps_taken": steps_taken,
        }

    # ── Single-action tasks: skip LLM evaluation for speed ────────────────
    # If the task is clearly a single action (no "and", "then", etc.), skip.
    task_lower = task.lower()
    multi_step_signals = [" and ", " then ", " after that", " also ", " next ", ", then"]
    is_likely_multi_step = any(sig in task_lower for sig in multi_step_signals)

    if not is_likely_multi_step and steps_taken >= 1:
        # Simple single-action task — done after first execution
        return {
            "remaining_task": "",
            "steps_taken": steps_taken,
        }

    # ── LLM evaluation for multi-step tasks ──────────────────────────────
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(EvalDecision)

    # Build a summary of what's been done so far
    history = "\n".join(
        f"  Step {i+1}: {r}" for i, r in enumerate(step_results)
    )
    if latest_result and latest_result not in (step_results[-1] if step_results else ""):
        history += f"\n  Step {len(step_results)+1}: {latest_result}"

    prompt = f"""You are the Task Evaluator of AutoOS, a desktop assistant.

ORIGINAL USER REQUEST: "{task}"

STEPS COMPLETED SO FAR:
{history or "  (none)"}

QUESTION: Is the ORIGINAL user request FULLY accomplished?

RULES:
1. If the user asked for multiple things (e.g. "open X and do Y"), check ALL parts.
2. If any part is still pending, set is_complete=False and describe what remains.
3. If everything is done, set is_complete=True.
4. Be strict: "open calculator" is complete after launch. "open calculator and compute 5+3" needs two steps.
5. If a step failed, consider the task incomplete only if a retry would help.
"""

    try:
        decision: EvalDecision = await invoke_with_fallback(structured_llm, prompt)
    except Exception as e:
        logger.error("Evaluator LLM failed: %s — defaulting to complete", e)
        return {
            "remaining_task": "",
            "steps_taken": steps_taken,
        }

    logger.info(
        "Evaluator: complete=%s remaining='%s' reason='%s'",
        decision.is_complete, decision.remaining_task, decision.reasoning,
    )

    if not decision.is_complete and decision.remaining_task:
        await emit_event(config, {
            "type": "step_info",
            "description": f"Step {steps_taken} done. Next: {decision.remaining_task}",
        })

    return {
        "remaining_task": "" if decision.is_complete else decision.remaining_task,
        "steps_taken": steps_taken,
    }


# ── Routing function for the conditional edge ────────────────────────────────

def should_continue(state: AgentState) -> str:
    """
    Conditional edge function: returns "continue" or "end".
    """
    remaining = state.get("remaining_task", "")
    steps = state.get("steps_taken", 0)

    if remaining and steps < MAX_AGENT_STEPS:
        logger.info("Loop continuing: step %d, remaining='%s'", steps, remaining)
        return "continue"

    logger.info("Loop ending after %d steps", steps)
    return "end"
