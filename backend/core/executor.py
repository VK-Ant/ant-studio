"""
Ant Studio — Workflow Executor
Topological sort + execute nodes in dependency order.
Error handling: failed nodes don't crash the pipeline.
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional, Callable

from .base_node import NodeResult, NodeStatus, ExecutionContext
from .workflow import Workflow, WorkflowNode, Connection
from .node_registry import registry

logger = logging.getLogger("antstudio.executor")


class WorkflowExecutor:

    async def execute(
        self,
        workflow: Workflow,
        context: Optional[ExecutionContext] = None,
    ) -> Dict[str, NodeResult]:
        """Execute all nodes in topological order."""

        if context is None:
            context = ExecutionContext(
                workflow_id=workflow.id,
                execution_id=str(uuid.uuid4()),
            )

        order = self._topological_sort(workflow)
        results: Dict[str, NodeResult] = {}
        total_start = time.time()

        logger.info(f"Executing workflow '{workflow.name}' ({len(order)} nodes)")

        for node_instance in order:
            # Check if upstream dependency failed
            if self._should_skip(node_instance, workflow.connections, results):
                results[node_instance.instance_id] = NodeResult(
                    outputs={},
                    status=NodeStatus.SKIPPED,
                    message="Skipped: upstream node failed",
                )
                await self._notify(context, node_instance.instance_id, "skipped", 0, "Skipped")
                continue

            # Instantiate node from registry
            try:
                node = registry.get(node_instance.node_type)
            except KeyError as e:
                results[node_instance.instance_id] = NodeResult(
                    outputs={}, status=NodeStatus.ERROR, message=str(e)
                )
                await self._notify(context, node_instance.instance_id, "error", 0, str(e))
                continue

            # Resolve inputs from upstream connections
            inputs = self._resolve_inputs(node_instance, workflow.connections, results)

            # Notify: running
            await self._notify(context, node_instance.instance_id, "running")

            # Execute
            start = time.time()
            try:
                result = await node.execute(inputs, node_instance.config, context)
                result.execution_time_ms = (time.time() - start) * 1000
            except Exception as e:
                logger.error(f"Node {node_instance.instance_id} ({node_instance.node_type}) failed: {e}")
                result = NodeResult(
                    outputs={},
                    status=NodeStatus.ERROR,
                    message=f"{type(e).__name__}: {str(e)}",
                    execution_time_ms=(time.time() - start) * 1000,
                )

            results[node_instance.instance_id] = result

            # Notify: completed
            await self._notify(
                context,
                node_instance.instance_id,
                result.status.value,
                result.execution_time_ms,
                result.message,
            )

            logger.info(
                f"  {node_instance.node_type} [{node_instance.instance_id}]: "
                f"{result.status.value} ({result.execution_time_ms:.0f}ms)"
            )

        total_ms = (time.time() - total_start) * 1000
        logger.info(f"Workflow complete in {total_ms:.0f}ms")

        return results

    def _topological_sort(self, wf: Workflow) -> list:
        """Kahn's algorithm for execution order."""
        node_ids = [n.instance_id for n in wf.nodes]
        in_degree = {nid: 0 for nid in node_ids}
        adj: Dict[str, list] = {nid: [] for nid in node_ids}

        for c in wf.connections:
            if c.source in adj and c.target in in_degree:
                adj[c.source].append(c.target)
                in_degree[c.target] += 1

        queue = [nid for nid, d in in_degree.items() if d == 0]
        order = []

        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for neighbor in adj.get(nid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Add any unconnected nodes at the end
        for nid in node_ids:
            if nid not in order:
                order.append(nid)

        node_map = {n.instance_id: n for n in wf.nodes}
        return [node_map[nid] for nid in order if nid in node_map]

    def _resolve_inputs(
        self,
        node: WorkflowNode,
        connections: list,
        results: Dict[str, NodeResult],
    ) -> Dict[str, Any]:
        """Gather outputs from upstream nodes into this node's inputs."""
        inputs: Dict[str, Any] = {}
        for conn in connections:
            if conn.target == node.instance_id:
                upstream = results.get(conn.source)
                if upstream and upstream.status == NodeStatus.SUCCESS:
                    value = upstream.outputs.get(conn.source_port)
                    inputs[conn.target_port] = value
        return inputs

    def _should_skip(
        self,
        node: WorkflowNode,
        connections: list,
        results: Dict[str, NodeResult],
    ) -> bool:
        """Skip if any required upstream node failed."""
        for conn in connections:
            if conn.target == node.instance_id:
                upstream = results.get(conn.source)
                if upstream and upstream.status == NodeStatus.ERROR:
                    return True
        return False

    async def _notify(
        self,
        context: ExecutionContext,
        node_id: str,
        status: str,
        time_ms: float = 0,
        message: str = "",
    ):
        """Send status update via callback if available."""
        if context.on_status:
            try:
                await context.on_status({
                    "type": "node_status",
                    "node_id": node_id,
                    "status": status,
                    "time_ms": time_ms,
                    "message": message,
                })
            except Exception:
                pass
