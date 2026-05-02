import os
import uuid
import logging
import asyncio
from typing import Dict
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
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

# ── Static Files ─────────────────────────────────────────────────────────────
os.makedirs(os.path.join(os.path.dirname(__file__), "screenshots"), exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "screenshots")), name="screenshots")

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
        return {"status": "stopped"}
    return {"status": "not_found"}        while True:
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
                # Let _run_agent_task's CancelledError handler notify the frontend
    except WebSocketDisconnect:
        # If the user closes the window, cancel any running task automatically
        task = _running_tasks.pop(execution_id, None)
        if task and not task.done():
            task.cancel()
        manager.disconnect(execution_id)
            elif data.get("type") == "stop":
                task = _running_tasks.pop(execution_id, None)
                if task and not task.done():
                    task.cancel()
                    logger.info("Cancelled execution %s via WebSocket stop message", execution_id)            "messages": [],
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
        try:
            await manager.send_message(execution_id, {
                "type": "stopped",
                "message": "Task stopped by user.",
            })
        except Exception:
            # WebSocket may already be closed
            pass    except Exception as e:
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

@app.get("/system/health")
async def get_system_health():
    import psutil
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    
    return {
        "cpu": cpu,
        "ram": ram,
        "battery": {
            "percent": battery.percent if battery else 100,
            "power_plugged": battery.power_plugged if battery else True
        } if battery else None,
        "disk": psutil.disk_usage('/').percent
    }

async def background_heartbeat():
    """
    Proactive Guardian Mode: Checks system status every 60 seconds 
    and broadcasts alerts to the UI.
    """
    import psutil
    while True:
        try:
            # Check CPU
            cpu = psutil.cpu_percent(interval=1)
            if cpu > 90:
                await manager.broadcast({
                    "type": "guardian_alert", 
                    "message": f"High CPU Load detected ({cpu}%). Suggest closing background apps."
                })
            
            # Check Battery
            battery = psutil.sensors_battery()
            if battery and battery.percent < 20 and not battery.power_plugged:
                await manager.broadcast({
                    "type": "guardian_alert",
                    "message": f"Low Battery ({battery.percent}%). Please connect a charger."
                })
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
        
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    # Start the proactive guardian heartbeat
    asyncio.create_task(background_heartbeat())

@app.post("/system/processes/kill")
async def kill_process_api(data: dict):
    from server.agent.nodes.executor import kill_process
    target = data.get("target")
    if not target:
        raise HTTPException(status_code=400, detail="Missing target process name or PID")
    
    result = kill_process(str(target))
    if "Failed" in result or "No active" in result:
        raise HTTPException(status_code=400, detail=result)
    return {"message": result}

from pathlib import Path
from datetime import datetime
import json

@app.post("/system/threads/save")
async def save_thread(data: dict):
    thread_id = data.get("id", "default")
    messages = data.get("messages", [])
    
    thread_path = Path("server/knowledge/threads")
    thread_path.mkdir(parents=True, exist_ok=True)
    
    with open(thread_path / f"{thread_id}.json", "w") as f:
        json.dump({
            "id": thread_id,
            "last_updated": datetime.now().isoformat(),
            "messages": messages
        }, f, indent=2)
    
    return {"status": "saved"}

@app.get("/system/threads/latest")
async def get_latest_thread():
    thread_path = Path("server/knowledge/threads")
    if not thread_path.exists():
        return {"messages": [], "id": "new-" + datetime.now().strftime("%Y%m%d%H%M%S")}
    
    files = list(thread_path.glob("*.json"))
    if not files:
        return {"messages": [], "id": "new-" + datetime.now().strftime("%Y%m%d%H%M%S")}
    
    # Sort by modification time
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    with open(latest_file, "r") as f:
        return json.load(f)

@app.get("/system/threads")
async def list_threads():
    thread_path = Path("server/knowledge/threads")
    if not thread_path.exists(): return []
    
    threads = []
    for f in thread_path.glob("*.json"):
        with open(f, "r") as tf:
            data = json.load(tf)
            threads.append({
                "id": data["id"],
                "last_updated": data["last_updated"],
                "preview": data["messages"][0]["content"] if data["messages"] else "Empty Chat"
            })
    return sorted(threads, key=lambda x: x["last_updated"], reverse=True)

@app.get("/system/workflows")
async def list_workflows():
    wf_path = Path("server/knowledge/workflows")
    if not wf_path.exists(): return []
    
    workflows = []
    for f in wf_path.glob("*.json"):
        with open(f, "r") as wf:
            workflows.append(json.load(wf))
    return workflows

@app.post("/system/workflows/save")
async def save_workflow(data: dict):
    wf_path = Path("server/knowledge/workflows")
    wf_path.mkdir(parents=True, exist_ok=True)
    
    wf_id = data.get("id", "wf_" + datetime.now().strftime("%H%M%S"))
    with open(wf_path / f"{wf_id}.json", "w") as f:
        json.dump(data, f, indent=2)
    return {"status": "saved"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("AUTOFLOW_PORT", 8765))
    uvicorn.run(app, host="0.0.0.0", port=port)
