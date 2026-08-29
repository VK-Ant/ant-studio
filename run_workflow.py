#!/usr/bin/env python3
"""CLI: Run a workflow from JSON file."""
import asyncio, sys, json, logging
from backend.core.workflow import Workflow
from backend.core.executor import WorkflowExecutor
from backend.core.base_node import ExecutionContext
from backend.nodes.register import register_all_nodes

logging.basicConfig(level="INFO", format="%(asctime)s [%(name)s] %(message)s")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python run_workflow.py <workflow.json>")
        sys.exit(1)

    register_all_nodes()
    wf = Workflow.from_json(sys.argv[1])
    print(f"\nExecuting: {wf.name} ({len(wf.nodes)} nodes)\n{'='*50}")

    executor = WorkflowExecutor()
    results = await executor.execute(wf)

    print(f"\n{'='*50}\nResults:\n")
    for nid, r in results.items():
        print(f"  {nid}: {r.status.value} ({r.execution_time_ms:.0f}ms) — {r.message}")
        if r.outputs:
            for k, v in r.outputs.items():
                display = str(v)[:200] if v is not None else "None"
                print(f"    {k}: {display}")
    print()

if __name__ == "__main__":
    asyncio.run(main())
