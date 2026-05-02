import os
import uuid
import logging
import asyncio
from typing import Dict, List
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent.graph import app_graph
from agent.bus import manager, emit_event
from server.routers.voice import router as voice_router
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoOS")

load_dotenv(Path(__file__).with_name(".env"), override=True)
load_dotenv(override=True)

app = FastAPI(title="AutoOS Gateway API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router)

class TaskRequest(BaseModel):
    task: str
    headless: bool | None = None
    input_values: dict[str, str] | None = None
    max_steps: int | None = None

class TaskResponse(BaseModel):
    status: str
    classification: str
    result: str

@app.post("/executions")
async def create_execution(request: TaskRequest):
    execution_id = str(uuid.uuid4())
    # We run the graph in the background after WS connects
    return {"id": execution_id}

@app.websocket("/ws/execution/{execution_id}")
async def websocket_endpoint(websocket: WebSocket, execution_id: str):
    await manager.connect(execution_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "start":
                task = data.get("task")
                # We can pull headless/max_steps from initial POST if we had persistence
                # For now, we'll just run with defaults or the message data
                await run_agent_task(execution_id, task, data)
    except WebSocketDisconnect:
        manager.disconnect(execution_id)
    except Exception as e:
        logger.error(f"WS Error: {e}")
        manager.disconnect(execution_id)

async def run_agent_task(execution_id: str, task: str, params: dict = None):
    try:
        # Initial state
        initial_state = {
            "task": task,
            "messages": [],
            "next_action": "",
            "plan": [],
            "result": "",
            "execution_id": execution_id,
            "headless": params.get("headless") if params else None,
            "max_steps": params.get("max_steps") if params else None,
            "input_values": params.get("input_values") if params else None,
        }
        
        # Run the graph
        await app_graph.ainvoke(
            initial_state, 
            config={"configurable": {"execution_id": execution_id}}
        )
        
    except Exception as e:
        await manager.send_message(execution_id, {"type": "step_error", "error": str(e)})

@app.post("/api/automate/task", response_model=TaskResponse)
async def automate_browser_task(request: TaskRequest):
    """
    Extension-friendly direct browser automation endpoint.

    This bypasses classification and executes the supplied task with browser-use.
    """
    from agent.tools.browser_tool import BrowserAutomationRunner

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
    uvicorn.run(app, host="0.0.0.0", port=port)
