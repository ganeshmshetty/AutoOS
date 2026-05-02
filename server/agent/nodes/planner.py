import os
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from server.agent.state import AgentState

class Classification(BaseModel):
    next_action: str = Field(description="The classification of the task: 'browser' or 'os'")
    reasoning: str = Field(description="Brief reasoning for the classification")

async def planner(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Analyzes the task and decides if it's a Browser or OS request.
    """
    task = state.get("task", "")
    if not task:
        return {"next_action": "end", "result": "No task provided"}

    # Initialize LLM
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key and os.getenv("LLM_API_KEYS"):
        api_key = os.getenv("LLM_API_KEYS").split(",")[0]

    model_name = os.getenv("LLM_MODEL", "gemini-3.1-flash-lite-preview")
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key
    )

    structured_llm = llm.with_structured_output(Classification)

    prompt = f"""
    You are the AutoOS Gateway Planner. Your job is to classify user requests into two categories:
    1. 'browser': Any task that requires navigating the web, searching online, or interacting with a website.
    2. 'os': Any task that involves local files, system settings, desktop applications (other than a browser), or system diagnostics.

    User Request: "{task}"

    Classify this request.
    """

    prediction = await structured_llm.ainvoke(prompt)
    
    # Emit event
    from server.agent.bus import emit_event
    await emit_event(config, {
        "type": "classification",
        "category": prediction.next_action
    })

    return {
        "next_action": prediction.next_action,
        "messages": [{"role": "assistant", "content": f"Classification: {prediction.next_action}. Reasoning: {prediction.reasoning}"}]
    }
