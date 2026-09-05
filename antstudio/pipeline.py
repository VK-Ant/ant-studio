"""Pipeline tracker — Kubeflow-style step tracking, logging, visualization."""
import time, json, os, uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

RUNS_DIR = Path.home() / ".antstudio" / "runs"


class Step:
    """A single pipeline step with status tracking."""
    def __init__(self, name: str, node_type: str, config: dict = None):
        self.name = name
        self.node_type = node_type
        self.config = config or {}
        self.status = "pending"    # pending → running → success / failed / skipped
        self.start_time = None
        self.end_time = None
        self.duration_ms = 0
        self.inputs = {}
        self.outputs = {}
        self.error = ""
        self.quality_score = None
        self.logs = []

    def start(self):
        self.status = "running"
        self.start_time = time.time()
        self.log(f"Started: {self.name}")

    def succeed(self, outputs: dict = None, message: str = ""):
        self.status = "success"
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000)
        self.outputs = outputs or {}
        self.log(f"Success: {message or self.name} ({self.duration_ms}ms)")

    def fail(self, error: str):
        self.status = "failed"
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - (self.start_time or time.time())) * 1000)
        self.error = error
        self.log(f"Failed: {error}")

    def skip(self, reason: str = "upstream failed"):
        self.status = "skipped"
        self.log(f"Skipped: {reason}")

    def log(self, message: str):
        self.logs.append({"time": datetime.now().isoformat(), "message": message})

    def to_dict(self):
        return {
            "name": self.name, "node_type": self.node_type, "status": self.status,
            "duration_ms": self.duration_ms, "error": self.error,
            "quality_score": self.quality_score,
            "config": self.config, "outputs_summary": {k: str(v)[:100] for k, v in self.outputs.items()},
            "logs": self.logs,
        }


class Pipeline:
    """Kubeflow-style pipeline with step tracking."""

    def __init__(self, name: str):
        self.name = name
        self.run_id = str(uuid.uuid4())[:8]
        self.steps: List[Step] = []
        self.connections: List[tuple] = []
        self.start_time = None
        self.end_time = None
        self.status = "pending"
        self.on_step_update: Optional[Callable] = None

    def add_step(self, name: str, node_type: str, config: dict = None) -> Step:
        step = Step(name, node_type, config)
        self.steps.append(step)
        return step

    def connect(self, source: str, target: str):
        self.connections.append((source, target))

    def run_step(self, step: Step, func: Callable, **kwargs) -> Any:
        """Execute a step with full tracking."""
        step.start()
        self._notify(step)
        try:
            result = func(**kwargs)
            step.succeed(outputs=result if isinstance(result, dict) else {"result": result})
            self._notify(step)
            return result
        except Exception as e:
            step.fail(str(e))
            self._notify(step)
            return None

    def start(self):
        self.start_time = time.time()
        self.status = "running"

    def finish(self):
        self.end_time = time.time()
        failed = any(s.status == "failed" for s in self.steps)
        self.status = "failed" if failed else "success"
        self._save_run()

    def _notify(self, step: Step):
        if self.on_step_update:
            self.on_step_update(step)

    def _save_run(self):
        try:
            RUNS_DIR.mkdir(parents=True, exist_ok=True)
            run_data = {
                "run_id": self.run_id, "name": self.name, "status": self.status,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round((self.end_time or time.time()) - (self.start_time or time.time()), 2),
                "steps": [s.to_dict() for s in self.steps],
                "connections": self.connections,
                "summary": {
                    "total": len(self.steps),
                    "success": sum(1 for s in self.steps if s.status == "success"),
                    "failed": sum(1 for s in self.steps if s.status == "failed"),
                    "skipped": sum(1 for s in self.steps if s.status == "skipped"),
                },
            }
            path = RUNS_DIR / f"{self.run_id}.json"
            path.write_text(json.dumps(run_data, indent=2))
        except Exception:
            pass

    def print_status(self):
        """Print Kubeflow-style pipeline visualization."""
        total_ms = sum(s.duration_ms for s in self.steps)
        icons = {"success": "+", "failed": "x", "running": "~", "pending": ".", "skipped": "-"}
        print(f"\n  Pipeline: {self.name} [{self.run_id}]")
        print(f"  {'='*60}")
        for i, step in enumerate(self.steps):
            icon = icons.get(step.status, "?")
            dur = f"{step.duration_ms}ms" if step.duration_ms else ""
            qual = f"q:{step.quality_score['score']:.2f}" if step.quality_score else ""
            err = f" ({step.error[:40]})" if step.error else ""
            connector = "  |" if i < len(self.steps) - 1 else "  "

            if step.status == "success":
                print(f"  [{icon}] {step.name:<30} {dur:>8}  {qual}{err}")
            elif step.status == "failed":
                print(f"  [{icon}] {step.name:<30} FAILED{err}")
            elif step.status == "skipped":
                print(f"  [{icon}] {step.name:<30} SKIPPED{err}")
            else:
                print(f"  [{icon}] {step.name:<30}")
            if i < len(self.steps) - 1:
                print(f"  {'|':>4}")
                print(f"  {'v':>4}")

        print(f"  {'='*60}")
        ok = sum(1 for s in self.steps if s.status == "success")
        fail = sum(1 for s in self.steps if s.status == "failed")
        print(f"  {ok}/{len(self.steps)} passed | {total_ms}ms total | Status: {self.status.upper()}\n")


def list_runs(limit: int = 20) -> List[dict]:
    """List past pipeline runs."""
    runs = []
    if RUNS_DIR.exists():
        for f in sorted(RUNS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)[:limit]:
            try:
                runs.append(json.loads(f.read_text()))
            except Exception:
                pass
    return runs


def get_run(run_id: str) -> Optional[dict]:
    """Get detailed run info."""
    path = RUNS_DIR / f"{run_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    # Search by prefix
    if RUNS_DIR.exists():
        for f in RUNS_DIR.glob(f"{run_id}*.json"):
            return json.loads(f.read_text())
    return None
