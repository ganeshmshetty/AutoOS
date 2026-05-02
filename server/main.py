import os
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from server.agent.graph import app_graph
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoOS")

load_dotenv(Path(__file__).with_name(".env"))
load_dotenv()

app = FastAPI(title="AutoOS Gateway API")

class TaskRequest(BaseModel):
    task: str
    headless: bool | None = None
    input_values: dict[str, str] | None = None
    max_steps: int | None = None

class TaskResponse(BaseModel):
    status: str
    classification: str
    result: str

@app.post("/execute", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """
    Endpoint to receive user input and route it through the Gateway.
    """
    logger.info(f"Received task: {request.task}")
    try:
        # Initial state
        initial_state = {
            "task": request.task,
            "messages": [],
            "next_action": "",
            "plan": [],
            "result": "",
            "headless": request.headless,
            "input_values": request.input_values,
            "max_steps": request.max_steps,
        }
        
        # Run the graph
        logger.info("Executing LangGraph...")
        final_state = await app_graph.ainvoke(initial_state)
        
        classification = final_state.get("next_action", "unknown")
        result = final_state.get("result", "No result generated")
        
        logger.info(f"Task complete. Classification: {classification}")
        
        return TaskResponse(
            status="success",
            classification=classification,
            result=result
        )
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/automate/task", response_model=TaskResponse)
async def automate_browser_task(request: TaskRequest):
    """
    Extension-friendly direct browser automation endpoint.

    This bypasses classification and executes the supplied task with browser-use.
    """
    from server.agent.tools.browser_tool import BrowserAutomationRunner

    try:
        logger.info(f"Received browser automation task: {request.task}")
        result = await BrowserAutomationRunner(headless=request.headless).run_task(
            request.task,
            sensitive_data=request.input_values,
            max_steps=request.max_steps,
        )
        return TaskResponse(
            status="success" if result.success else "failed",
            classification="browser",
            result=result.as_text(),
        )
    except Exception as e:
        logger.error(f"Error during browser automation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AUTOFLOW_PORT", 8765))
    logger.info(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
