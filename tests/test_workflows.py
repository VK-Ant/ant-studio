"""Integration tests — full workflow execution."""
import asyncio, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.workflow import Workflow
from backend.core.executor import WorkflowExecutor
from backend.core.base_node import ExecutionContext, NodeStatus
from backend.nodes.register import register_all_nodes
register_all_nodes()

def _run(wf):
    ctx = ExecutionContext(workflow_id="test", execution_id="integ")
    return asyncio.run(WorkflowExecutor().execute(wf, ctx))

def test_invoice_extraction():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("INVOICE\nVendor: TestCorp\nInvoice Number: INV-001\nAmount: $5000\nDate: 2026-01-01\n")
        path = f.name
    try:
        wf = Workflow.from_dict({"id":"t1","name":"Invoice","nodes":[
            {"instance_id":"input","node_type":"file_input","config":{"path":path}},
            {"instance_id":"extract","node_type":"docqwise_extract","config":{"fields":"vendor,amount,invoice_number"}},
            {"instance_id":"eval","node_type":"evaluate","config":{"threshold":0.1}},
        ],"connections":[
            {"source":"input","source_port":"content","target":"extract","target_port":"text"},
            {"source":"extract","source_port":"fields","target":"eval","target_port":"answer"},
        ]})
        r = _run(wf)
        assert r["input"].status == NodeStatus.SUCCESS
        assert r["extract"].status == NodeStatus.SUCCESS
        assert r["extract"].outputs["fields"]["vendor"] == "TestCorp"
        assert r["eval"].status == NodeStatus.SUCCESS
    finally:
        os.unlink(path)

def test_forecasting():
    import random; random.seed(42)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("date,value\n" + "\n".join(f"2025-01-{i+1:02d},{100+random.gauss(0,10):.1f}" for i in range(28)))
        path = f.name
    try:
        wf = Workflow.from_dict({"id":"t2","name":"FC","nodes":[
            {"instance_id":"input","node_type":"file_input","config":{"path":path}},
            {"instance_id":"load","node_type":"data_loader","config":{"target":"value","time_col":"date"}},
            {"instance_id":"fc","node_type":"forecast","config":{"model":"arima","horizon":7,"target":"value"}},
        ],"connections":[
            {"source":"input","source_port":"file_path","target":"load","target_port":"file_path"},
            {"source":"load","source_port":"data","target":"fc","target_port":"data"},
        ]})
        r = _run(wf)
        assert r["load"].status == NodeStatus.SUCCESS
        assert r["load"].outputs["row_count"] == 28
        assert r["fc"].status == NodeStatus.SUCCESS
        assert len(r["fc"].outputs["forecast"]["prediction"]) == 7
    finally:
        os.unlink(path)

def test_anomaly_detection():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        vals = [100+i*0.1 for i in range(50)]; vals[25] = 500
        f.write("date,temp\n" + "\n".join(f"2025-01-{i+1:02d},{v}" for i,v in enumerate(vals)))
        path = f.name
    try:
        wf = Workflow.from_dict({"id":"t3","name":"Anom","nodes":[
            {"instance_id":"input","node_type":"file_input","config":{"path":path}},
            {"instance_id":"load","node_type":"data_loader","config":{"target":"temp"}},
            {"instance_id":"anom","node_type":"anomaly_detect","config":{"target":"temp","threshold":2.0}},
        ],"connections":[
            {"source":"input","source_port":"file_path","target":"load","target_port":"file_path"},
            {"source":"load","source_port":"data","target":"anom","target_port":"data"},
        ]})
        r = _run(wf)
        assert r["anom"].status == NodeStatus.SUCCESS
        assert r["anom"].outputs["anomaly_count"] >= 1
    finally:
        os.unlink(path)

def test_audit_pipeline():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Vendor: Acme\nAmount: $1000\n"); path = f.name
    try:
        wf = Workflow.from_dict({"id":"t4","name":"Audit","nodes":[
            {"instance_id":"guard","node_type":"guard_start","config":{}},
            {"instance_id":"input","node_type":"file_input","config":{"path":path}},
            {"instance_id":"extract","node_type":"docqwise_extract","config":{"fields":"vendor"}},
            {"instance_id":"audit","node_type":"guard_report","config":{}},
        ],"connections":[
            {"source":"input","source_port":"content","target":"extract","target_port":"text"},
            {"source":"guard","source_port":"guard_session","target":"audit","target_port":"guard_session"},
        ]})
        r = _run(wf)
        assert r["guard"].status == NodeStatus.SUCCESS
        assert r["audit"].status == NodeStatus.SUCCESS
        assert r["audit"].outputs["data_left_system"] is False
    finally:
        os.unlink(path)

def test_confidence_routing():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Some random text without structured fields"); path = f.name
    try:
        wf = Workflow.from_dict({"id":"t5","name":"Route","nodes":[
            {"instance_id":"input","node_type":"file_input","config":{"path":path}},
            {"instance_id":"extract","node_type":"docqwise_extract","config":{"fields":"vendor,amount"}},
            {"instance_id":"eval","node_type":"evaluate","config":{"threshold":0.1}},
            {"instance_id":"gate","node_type":"confidence_gate","config":{"threshold":0.9}},
            {"instance_id":"review","node_type":"human_review","config":{"auto_approve":True}},
        ],"connections":[
            {"source":"input","source_port":"content","target":"extract","target_port":"text"},
            {"source":"extract","source_port":"fields","target":"eval","target_port":"answer"},
            {"source":"eval","source_port":"score","target":"gate","target_port":"score"},
            {"source":"extract","source_port":"fields","target":"gate","target_port":"data"},
            {"source":"gate","source_port":"fail_data","target":"review","target_port":"data"},
        ]})
        r = _run(wf)
        assert r["gate"].status == NodeStatus.SUCCESS
        assert r["gate"].outputs["passed"] is False  # low confidence fails 0.9 gate
    finally:
        os.unlink(path)

def test_template_files():
    tdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
    for f in os.listdir(tdir):
        if f.endswith(".json"):
            wf = Workflow.from_json(os.path.join(tdir, f))
            assert wf.name and len(wf.nodes) > 0, f"Template {f} invalid"

def test_save_reload():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f: path = f.name
    try:
        wf = Workflow.from_dict({"id":"s","name":"Save","nodes":[{"instance_id":"n1","node_type":"file_input","config":{"path":"/x"}}],"connections":[]})
        wf.to_json(path)
        wf2 = Workflow.from_json(path)
        assert wf2.name == "Save"
    finally:
        os.unlink(path)
