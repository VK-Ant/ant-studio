"""Tests for Ant Studio core framework — base_node, registry, workflow, executor."""
import asyncio
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus, ExecutionContext
from backend.core.node_registry import NodeRegistry
from backend.core.workflow import Workflow, WorkflowNode, Connection
from backend.core.executor import WorkflowExecutor
from backend.core.resource_manager import ResourceManager


# ============================================================
# BASE NODE TESTS
# ============================================================

class DummyNode(BaseNode):
    node_type = "dummy"
    label = "Dummy Node"
    category = "test"
    description = "Test node"

    def define_inputs(self):
        return [Port("input_text", PortType.TEXT, "Input")]

    def define_outputs(self):
        return [Port("output_text", PortType.TEXT, "Output")]

    def define_config(self):
        return [NodeConfig("prefix", "Prefix", "string", default="processed")]

    async def execute(self, inputs, config, context):
        text = inputs.get("input_text", "")
        prefix = config.get("prefix", "processed")
        return NodeResult(
            outputs={"output_text": f"{prefix}: {text}"},
            message=f"Processed with prefix '{prefix}'"
        )


class SourceNode(BaseNode):
    node_type = "source"
    label = "Source"
    category = "test"

    def define_inputs(self):
        return []

    def define_outputs(self):
        return [Port("data", PortType.TEXT, "Output data")]

    async def execute(self, inputs, config, context):
        return NodeResult(outputs={"data": config.get("value", "hello")})


class SinkNode(BaseNode):
    node_type = "sink"
    label = "Sink"
    category = "test"

    def define_inputs(self):
        return [Port("data", PortType.ANY, "Input")]

    def define_outputs(self):
        return [Port("received", PortType.TEXT, "What was received")]

    async def execute(self, inputs, config, context):
        return NodeResult(outputs={"received": str(inputs.get("data", "nothing"))})


class ErrorNode(BaseNode):
    node_type = "error_node"
    label = "Error Node"
    category = "test"

    def define_inputs(self):
        return [Port("input", PortType.ANY)]

    def define_outputs(self):
        return [Port("output", PortType.ANY)]

    async def execute(self, inputs, config, context):
        raise ValueError("Intentional test error")


# --- Base Node Tests ---

def test_base_node_manifest():
    node = DummyNode()
    m = node.to_manifest()
    assert m["node_type"] == "dummy"
    assert m["label"] == "Dummy Node"
    assert m["category"] == "test"
    assert len(m["inputs"]) == 1
    assert len(m["outputs"]) == 1
    assert len(m["config"]) == 1
    assert m["inputs"][0]["name"] == "input_text"
    assert m["inputs"][0]["type"] == "text"
    assert m["config"][0]["key"] == "prefix"
    assert m["config"][0]["default"] == "processed"


def test_base_node_execution():
    node = DummyNode()
    result = asyncio.run(node.execute(
        {"input_text": "hello world"},
        {"prefix": "test"},
        ExecutionContext()
    ))
    assert result.status == NodeStatus.SUCCESS
    assert result.outputs["output_text"] == "test: hello world"


def test_port_types():
    for pt in PortType:
        port = Port("test", pt)
        assert port.port_type == pt


# --- Registry Tests ---

def test_registry_register_and_get():
    reg = NodeRegistry()
    reg.register(DummyNode)
    node = reg.get("dummy")
    assert node.node_type == "dummy"
    assert isinstance(node, DummyNode)


def test_registry_unknown_node():
    reg = NodeRegistry()
    with pytest.raises(KeyError):
        reg.get("nonexistent")


def test_registry_list_manifests():
    reg = NodeRegistry()
    reg.register(DummyNode)
    reg.register(SourceNode)
    manifests = reg.list_manifests()
    assert len(manifests) == 2
    types = [m["node_type"] for m in manifests]
    assert "dummy" in types
    assert "source" in types


def test_registry_categories():
    reg = NodeRegistry()
    reg.register(DummyNode)
    reg.register(SourceNode)
    cats = reg.list_categories()
    assert "test" in cats
    assert len(cats["test"]) == 2


# --- Workflow Tests ---

def test_workflow_from_dict():
    data = {
        "id": "test_wf",
        "name": "Test",
        "nodes": [
            {"instance_id": "n1", "node_type": "source", "config": {"value": "hello"}},
            {"instance_id": "n2", "node_type": "dummy", "config": {"prefix": "out"}},
        ],
        "connections": [
            {"source": "n1", "source_port": "data", "target": "n2", "target_port": "input_text"}
        ]
    }
    wf = Workflow.from_dict(data)
    assert wf.name == "Test"
    assert len(wf.nodes) == 2
    assert len(wf.connections) == 1
    assert wf.nodes[0].node_type == "source"


def test_workflow_roundtrip():
    data = {
        "id": "rt",
        "name": "Roundtrip",
        "nodes": [{"instance_id": "n1", "node_type": "source", "config": {}}],
        "connections": []
    }
    wf = Workflow.from_dict(data)
    d = wf.to_dict()
    wf2 = Workflow.from_dict(d)
    assert wf2.name == wf.name
    assert len(wf2.nodes) == len(wf.nodes)


def test_workflow_json_file(tmp_path):
    data = {"id": "f", "name": "FileTest", "nodes": [{"instance_id": "n1", "node_type": "source", "config": {}}], "connections": []}
    wf = Workflow.from_dict(data)
    path = str(tmp_path / "test.json")
    wf.to_json(path)
    wf2 = Workflow.from_json(path)
    assert wf2.name == "FileTest"


# --- Executor Tests ---

def test_executor_simple_pipeline():
    from backend.core.node_registry import registry as global_reg
    global_reg.register(SourceNode)
    global_reg.register(DummyNode)
    

    wf = Workflow.from_dict({
        "id": "t1", "name": "Test",
        "nodes": [
            {"instance_id": "src", "node_type": "source", "config": {"value": "world"}},
            {"instance_id": "proc", "node_type": "dummy", "config": {"prefix": "hello"}},
        ],
        "connections": [
            {"source": "src", "source_port": "data", "target": "proc", "target_port": "input_text"}
        ]
    })

    executor = WorkflowExecutor()
    results = asyncio.run(executor.execute(wf))

    assert results["src"].status == NodeStatus.SUCCESS
    assert results["src"].outputs["data"] == "world"
    assert results["proc"].status == NodeStatus.SUCCESS
    assert results["proc"].outputs["output_text"] == "hello: world"



def test_executor_error_handling():
    from backend.core.node_registry import registry as global_reg
    try: global_reg.register(ErrorNode)
    except: pass
    try: global_reg.register(SinkNode)
    except: pass
    

    wf = Workflow.from_dict({
        "id": "t2", "name": "ErrorTest",
        "nodes": [
            {"instance_id": "src", "node_type": "source", "config": {}},
            {"instance_id": "err", "node_type": "error_node", "config": {}},
            {"instance_id": "sink", "node_type": "sink", "config": {}},
        ],
        "connections": [
            {"source": "src", "source_port": "data", "target": "err", "target_port": "input"},
            {"source": "err", "source_port": "output", "target": "sink", "target_port": "data"},
        ]
    })

    executor = WorkflowExecutor()
    results = asyncio.run(executor.execute(wf))

    assert results["src"].status == NodeStatus.SUCCESS
    assert results["err"].status == NodeStatus.ERROR
    assert "Intentional test error" in results["err"].message
    assert results["sink"].status == NodeStatus.SKIPPED



def test_executor_independent_branches():
    """Verify that an error in one branch doesn't affect another."""
    

    wf = Workflow.from_dict({
        "id": "t3", "name": "BranchTest",
        "nodes": [
            {"instance_id": "src1", "node_type": "source", "config": {"value": "good"}},
            {"instance_id": "src2", "node_type": "source", "config": {"value": "bad"}},
            {"instance_id": "err", "node_type": "error_node", "config": {}},
            {"instance_id": "sink1", "node_type": "sink", "config": {}},
            {"instance_id": "sink2", "node_type": "sink", "config": {}},
        ],
        "connections": [
            {"source": "src1", "source_port": "data", "target": "sink1", "target_port": "data"},
            {"source": "src2", "source_port": "data", "target": "err", "target_port": "input"},
            {"source": "err", "source_port": "output", "target": "sink2", "target_port": "data"},
        ]
    })

    executor = WorkflowExecutor()
    results = asyncio.run(executor.execute(wf))

    assert results["sink1"].status == NodeStatus.SUCCESS  # independent branch succeeded
    assert results["err"].status == NodeStatus.ERROR
    assert results["sink2"].status == NodeStatus.SKIPPED  # downstream of error



# --- Resource Manager Tests ---

def test_resource_manager_cache():
    rm = ResourceManager(max_memory_mb=1000)
    model = rm.get_model("test_model", lambda: ("mock_model", 100))
    assert model == "mock_model"
    assert "test_model" in rm.status()["models_loaded"]

    model2 = rm.get_model("test_model", lambda: ("should_not_load", 100))
    assert model2 == "mock_model"  # cached


def test_resource_manager_eviction():
    rm = ResourceManager(max_memory_mb=180)
    rm.get_model("m1", lambda: ("model1", 100))
    rm.get_model("m2", lambda: ("model2", 100))
    rm.get_model("m3", lambda: ("model3", 100))  # should evict m1

    status = rm.status()
    assert "m1" not in status["models_loaded"]
    assert "m3" in status["models_loaded"]


def test_resource_manager_unload():
    rm = ResourceManager()
    rm.get_model("x", lambda: ("mx", 50))
    assert "x" in rm.status()["models_loaded"]
    rm.unload("x")
    assert "x" not in rm.status()["models_loaded"]
