"""Ant Studio WebSocket — live execution updates."""
import uuid, json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.core.workflow import Workflow
from backend.core.executor import WorkflowExecutor
from backend.core.base_node import ExecutionContext
from backend.config import settings

ws_router = APIRouter()

@ws_router.websocket("/ws/execute")
async def execute_workflow(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        workflow = Workflow.from_dict(data)

        async def send_status(msg: dict):
            await websocket.send_json(msg)

        ctx = ExecutionContext(
            workflow_id=workflow.id,
            execution_id=str(uuid.uuid4()),
            data_dir=settings.DATA_DIR,
            on_status=send_status,
        )

        executor = WorkflowExecutor()
        results = await executor.execute(workflow, ctx)

        await websocket.send_json({
            "type": "workflow_complete",
            "execution_id": ctx.execution_id,
            "results": {
                nid: {"status": r.status.value, "message": r.message, "time_ms": r.execution_time_ms,
                       "outputs": {k: str(v)[:1000] if not isinstance(v, (int, float, bool, type(None))) else v
                                   for k, v in r.outputs.items()}}
                for nid, r in results.items()
            },
        })
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
