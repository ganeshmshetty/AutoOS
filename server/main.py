import os
import uuid
import logging
import asyncio
from typing import Dict
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from server.agent.graph import app_graph
from server.agent.bus import manager, emit_event
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoOS")

load_dotenv(Path(__file__).with_name(".env"), override=True)
load_dotenv(override=True)

app = FastAPI(title="AutoOS Gateway API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Running task registry ─────────────────────────────────────────────────────
# Maps execution_id → asyncio.Task so we can cancel it on demand.
_running_tasks: Dict[str, asyncio.Task] = {}


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
    return {"id": execution_id}


@app.post("/executions/{execution_id}/stop")
async def stop_execution(execution_id: str):
    """Cancel a running execution by its ID."""
    task = _running_tasks.pop(execution_id, None)
    if task and not task.done():
        task.cancel()
        logger.info("Cancelled execution %s via REST", execution_id)
        # Notify the frontend
        await manager.send_message(execution_id, {
            "type": "stopped",
            "message": "Task stopped by user.",
        })
        return {"status": "stopped"}
    return {"status": "not_found"}


@app.websocket("/ws/execution/{execution_id}")
async def websocket_endpoint(websocket: WebSocket, execution_id: str):
    await manager.connect(execution_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "start":
                task_text = data.get("task")
                # Run as a proper background task so the WS loop stays alive
                # and can receive a "stop" message while the agent is running.
                agent_task = asyncio.create_task(
                    _run_agent_task(execution_id, task_text, data)
                )
                _running_tasks[execution_id] = agent_task

                # When the task finishes (normally or cancelled) clean up registry
                def _cleanup(fut: asyncio.Task):
                    _running_tasks.pop(execution_id, None)

                agent_task.add_done_callback(_cleanup)

            elif data.get("type") == "stop":
                task = _running_tasks.pop(execution_id, None)
                if task and not task.done():
                    task.cancel()
                    logger.info("Cancelled execution %s via WebSocket stop message", execution_id)
                await manager.send_message(execution_id, {
                    "type": "stopped",
                    "message": "Task stopped by user.",
                })

    except WebSocketDisconnect:
        # If the user closes the window, cancel any running task automatically
        task = _running_tasks.pop(execution_id, None)
        if task and not task.done():
            task.cancel()
        manager.disconnect(execution_id)
    except Exception as e:
        logger.error("WS Error: %s", e)
        manager.disconnect(execution_id)


async def _run_agent_task(execution_id: str, task: str, params: dict | None = None):
    try:
        initial_state = {
            "task": task,
            "messages": [],
            "next_action": "",
            "sub_category": "",
            "entities": [],
            "action_params": {},
            "plain_english_plan": "",
            "confidence": 1.0,
            "needs_hitl": False,
            "plan": [],
            "result": "",
            "headless": params.get("headless") if params else None,
            "max_steps": params.get("max_steps") if params else None,
            "input_values": params.get("input_values") if params else None,
        }

        await app_graph.ainvoke(
            initial_state,
            config={"configurable": {"execution_id": execution_id}},
        )

    except asyncio.CancelledError:
        # Task was cancelled via the stop button — notify frontend
        logger.info("Agent task %s was cancelled", execution_id)
        await manager.send_message(execution_id, {
            "type": "stopped",
            "message": "Task stopped by user.",
        })
    except Exception as e:
        logger.error("Agent task error: %s", e, exc_info=True)
        await manager.send_message(execution_id, {"type": "step_error", "error": str(e)})


@app.post("/api/automate/task", response_model=TaskResponse)
async def automate_browser_task(request: TaskRequest):
    """Extension-friendly direct browser automation endpoint."""
    from server.agent.tools.browser_tool import BrowserAutomationRunner

    try:
        logger.info("Received browser automation task: %s", request.task)
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
        logger.error("Error during browser automation: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AUTOFLOW_PORT", 8765))
    uvicorn.run(app, host="0.0.0.0", port=port)
