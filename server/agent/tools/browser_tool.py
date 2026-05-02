import os
from browser_use import Agent
from langchain_google_genai import ChatGoogleGenerativeAI
from server.agent.state import AgentState

async def run_browser_task(task: str) -> str:
    """
    Executes a task using the browser-use library.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key and os.getenv("LLM_API_KEYS"):
        api_key = os.getenv("LLM_API_KEYS").split(",")[0]

    llm = ChatGoogleGenerativeAI(
        model=os.getenv("LLM_MODEL", "gemini-1.5-pro"),
        google_api_key=api_key
    )

    agent = Agent(
        task=task,
        llm=llm,
    )
    
    result = await agent.run()
    return result.final_result()
