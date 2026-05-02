import os
import uuid
import logging
import asyncio
from typing import Dict, List
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment before any other imports that may need env vars
load_dotenv(Path(__file__).with_name(".env"), override=True)

from agent.graph import app_graph
from agent.bus import manager, emit_event
from routers.voice import router as voice_router
from routers.face_auth import router as face_auth_router
from db import init_db, get_session
from models.workflow import Workflow
from fastapi import Depends, HTTPException
from sqlmodel import Session, select
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoOS")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="AutoOS Gateway API", lifespan=lifespan)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(voice_router)
app.include_router(face_auth_router)

# --- Workflow Endpoints ---

@app.post("/api/workflows", response_model=Workflow)
def create_workflow(workflow: Workflow, session: Session = Depends(get_session)):
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    return workflow

@app.get("/api/workflows", response_model=List[Workflow])
def list_workflows(session: Session = Depends(get_session)):
    return session.exec(select(Workflow).order_by(Workflow.created_at.desc())).all()

@app.get("/api/workflows/{workflow_id}", response_model=Workflow)
def get_workflow(workflow_id: str, session: Session = Depends(get_session)):
    workflow = session.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@app.delete("/api/workflows/{workflow_id}")
def delete_workflow(workflow_id: str, session: Session = Depends(get_session)):
    workflow = session.get(Workflow, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    session.delete(workflow)
    session.commit()
    return {"ok": True}

@app.post("/api/share")
async def share_workflow(workflow: dict):
    async with httpx.AsyncClient() as client:
        res = await client.post("https://jsonblob.com/api/jsonBlob", json=workflow)
        blob_id = res.headers.get("x-jsonblob-id")
        if not blob_id:
            location = res.headers.get("location")
            if location:
                blob_id = location.split("/")[-1]
        if not blob_id:
            raise HTTPException(status_code=500, detail="Failed to retrieve share ID from jsonblob")
        return {"blob_id": blob_id}

# --- Task Endpoints ---
class TaskRequest(BaseModel):
    task: str


class TaskResponse(BaseModel):
    status: str
    result: str


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "AutoOS Gateway"}


@app.post("/executions")
async def create_execution(request: TaskRequest):
    """Create a new execution session. Returns an ID to connect via WebSocket."""
    execution_id = str(uuid.uuid4())
    logger.info(f"Created execution {execution_id} for task: {request.task[:100]}")
    return {"id": execution_id}


# Track running tasks so we can cancel them on disconnect
active_tasks: Dict[str, asyncio.Task] = {}

@app.websocket("/ws/execution/{execution_id}")
async def websocket_endpoint(websocket: WebSocket, execution_id: str):
    """
    WebSocket endpoint for real-time execution events.
    
    Client connects, sends {"type": "start", "task": "..."} to begin.
    Server streams events: thinking, tool_call, tool_result, step_start, step_done, complete, etc.
    """
    await manager.connect(execution_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "start":
                task = data.get("task", "")
                logger.info(f"Starting execution {execution_id}: {task[:100]}")
                # Run the agent in the background so we can keep the WS alive
                active_tasks[execution_id] = asyncio.create_task(run_agent_task(execution_id, task))
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {execution_id}")
        manager.disconnect(execution_id)
        if execution_id in active_tasks:
            active_tasks[execution_id].cancel()
            del active_tasks[execution_id]
    except Exception as e:
        logger.error(f"WS Error: {e}", exc_info=True)
        manager.disconnect(execution_id)
        if execution_id in active_tasks:
            active_tasks[execution_id].cancel()
            del active_tasks[execution_id]


async def run_agent_task(execution_id: str, task: str):
    """Run the LangGraph agent loop for a task."""
    try:
        initial_state = {
            "task": task,
            "messages": [],
            "tool_history": [],
            "result": "",
            "execution_id": execution_id,
            "iteration": 0,
            "done": False,
        }

        # Run the graph
        result = await app_graph.ainvoke(
            initial_state,
            config={"configurable": {"execution_id": execution_id}}
        )

        logger.info(f"Execution {execution_id} completed")

        # If the graph ended without sending a "complete" event (e.g., max iterations),
        # send one now
        final_result = result.get("result", "Task completed.")
        if not result.get("done"):
            await manager.send_message(execution_id, {
                "type": "complete",
                "summary": final_result or "Task completed (max iterations reached).",
            })

    except Exception as e:
        logger.error(f"Agent task error: {e}", exc_info=True)
        await manager.send_message(execution_id, {
            "type": "step_error",
            "error": str(e),
        })
        await manager.send_message(execution_id, {
            "type": "complete",
            "summary": f"Task failed: {str(e)}",
        })


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AUTOFLOW_PORT", 8765))
    uvicorn.run(app, host="0.0.0.0", port=port)
