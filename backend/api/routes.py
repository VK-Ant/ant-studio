"""Ant Studio REST API routes."""
import os, json, uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.core.node_registry import registry
from backend.core.workflow import Workflow
from backend.core.executor import WorkflowExecutor
from backend.core.base_node import ExecutionContext
from backend.core.resource_manager import resources
from backend.config import settings

router = APIRouter()

@router.get("/nodes")
async def list_nodes():
    return {"nodes": registry.list_manifests(), "count": registry.count}

@router.get("/nodes/categories")
async def list_categories():
    return registry.list_categories()

@router.get("/templates")
async def list_templates():
    tdir = settings.TEMPLATES_DIR
    if not os.path.isdir(tdir):
        return {"templates": []}
    templates = []
    for f in os.listdir(tdir):
        if f.endswith(".json"):
            with open(os.path.join(tdir, f)) as fp:
                wf = json.load(fp)
                templates.append({"name": wf.get("name", f), "file": f, "description": wf.get("description", "")})
    return {"templates": templates}

@router.get("/templates/{name}")
async def get_template(name: str):
    path = os.path.join(settings.TEMPLATES_DIR, name if name.endswith(".json") else f"{name}.json")
    if not os.path.isfile(path):
        raise HTTPException(404, f"Template not found: {name}")
    with open(path) as f:
        return json.load(f)

@router.post("/workflows/run")
async def run_workflow(workflow_data: dict):
    wf = Workflow.from_dict(workflow_data)
    ctx = ExecutionContext(workflow_id=wf.id, execution_id=str(uuid.uuid4()), data_dir=settings.DATA_DIR)
    executor = WorkflowExecutor()
    results = await executor.execute(wf, ctx)
    return {
        "execution_id": ctx.execution_id,
        "results": {
            nid: {"status": r.status.value, "message": r.message, "time_ms": r.execution_time_ms,
                   "outputs": {k: str(v)[:500] if not isinstance(v, (int, float, bool, type(None))) else v
                               for k, v in r.outputs.items()}}
            for nid, r in results.items()
        },
    }

@router.post("/workflows/save")
async def save_workflow(workflow_data: dict):
    os.makedirs(settings.WORKFLOWS_DIR, exist_ok=True)
    wf = Workflow.from_dict(workflow_data)
    path = os.path.join(settings.WORKFLOWS_DIR, f"{wf.name.replace(' ', '_').lower()}.json")
    wf.to_json(path)
    return {"saved": path}

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    path = os.path.join(settings.DATA_DIR, file.filename)
    with open(path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"file_id": str(uuid.uuid4())[:8], "path": path, "size": len(content)}

@router.get("/resources")
async def get_resources():
    return resources.status()

@router.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0", "nodes": registry.count}
