import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger("AutoOS.desktop")

async def run_os_task(task: str, mode: str = "auto") -> str:
    """
    Executes a desktop automation task using Simular AI's Agent-S (gui-agents).
    """
    logger.info(f"Executing OS task with Agent-S: {task}")

    try:
        from gui_agents.s3.agent import AgentS3
        from gui_agents.s3.grounding import OSWorldACI
    except ImportError as e:
        logger.error(f"Failed to import gui-agents: {e}")
        return f"Error: gui-agents not installed properly. {e}"

    # Determine which model to use.
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    api_key = os.getenv("OPENAI_API_KEY") 

    if not api_key:
        gemini_key = os.getenv("GOOGLE_API_KEY")
        if gemini_key:
            api_key = gemini_key
            if "gemini" not in model_name:
                model_name = "gemini-1.5-pro-latest"
        else:
             return "Error: OPENAI_API_KEY or GOOGLE_API_KEY is required for Agent-S."

    engine_params = {
        "model": model_name,
        "api_key": api_key
    }

    try:
        # Wrap the synchronous Agent-S run in a thread so it doesn't block the async event loop
        loop = asyncio.get_running_loop()
        
        def _run_agent():
            logger.info("Initializing Agent-S Grounding Agent...")
            grounding_agent = OSWorldACI(engine_params=engine_params)
            
            logger.info("Initializing Agent-S Main Agent...")
            agent = AgentS3(
                engine_params=engine_params,
                grounding_agent=grounding_agent
            )
            
            logger.info(f"Running Agent-S task: {task}")
            # Agent-S typically logs to stdout/stderr.
            result = agent.run(task)
            return result

        result = await loop.run_in_executor(None, _run_agent)
        
        return f"Successfully executed OS task via Agent-S. Result: {result}"
        
    except Exception as e:
        logger.error(f"Failed to execute task via Agent-S: {str(e)}", exc_info=True)
        return f"Failed to complete task via Agent-S: {str(e)}"
