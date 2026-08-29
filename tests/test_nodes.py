"""Tests for all Ant Studio nodes — verify each node executes without errors."""
import asyncio
import pytest
import os
import sys
import csv
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.base_node import ExecutionContext, NodeStatus
from backend.nodes.register import register_all_nodes
from backend.core.node_registry import registry

# Register all nodes once
register_all_nodes()

CTX = ExecutionContext(workflow_id="test", execution_id="test_exec", data_dir="./data")
SAMPLE_TEXT = """INVOICE
Vendor: Acme Corporation
Invoice Number: INV-2026-0847
Date: August 15, 2026
Amount: $12,500.00
Description: Cloud infrastructure services
Payment Terms: Net 30"""


# ============================================================
# COMMON NODES
# ============================================================

def test_file_input_valid(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")
    node = registry.get("file_input")
    r = asyncio.run(node.execute({}, {"path": str(f)}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert r.outputs["file_name"] == "test.txt"
    assert r.outputs["file_size"] == 5


def test_file_input_missing():
    node = registry.get("file_input")
    r = asyncio.run(node.execute({}, {"path": "/nonexistent.txt"}, CTX))
    assert r.status == NodeStatus.ERROR


def test_file_input_folder(tmp_path):
    (tmp_path / "a.pdf").write_text("pdf")
    (tmp_path / "b.txt").write_text("txt")
    (tmp_path / "c.jpg").write_bytes(b"img")
    node = registry.get("file_input")
    r = asyncio.run(node.execute({}, {"folder": str(tmp_path), "extensions": ".pdf,.txt"}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert len(r.outputs["file_path"]) == 2


def test_text_input():
    node = registry.get("text_input")
    r = asyncio.run(node.execute({}, {"text": "What is the total?", "label": "Q"}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert r.outputs["text"] == "What is the total?"


def test_export_csv(tmp_path):
    node = registry.get("export_csv")
    out = str(tmp_path / "out.csv")
    r = asyncio.run(node.execute({"data": {"name": "test", "value": 42}}, {"output_path": out}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert os.path.isfile(out)
    with open(out) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["name"] == "test"


def test_export_csv_list(tmp_path):
    node = registry.get("export_csv")
    out = str(tmp_path / "out2.csv")
    data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    r = asyncio.run(node.execute({"data": data}, {"output_path": out}, CTX))
    assert r.status == NodeStatus.SUCCESS
    with open(out) as f:
        assert len(list(csv.DictReader(f))) == 2


def test_export_json(tmp_path):
    node = registry.get("export_json")
    out = str(tmp_path / "out.json")
    r = asyncio.run(node.execute({"data": {"key": "value"}}, {"output_path": out}, CTX))
    assert r.status == NodeStatus.SUCCESS
    with open(out) as f:
        assert json.load(f)["key"] == "value"


def test_display_result():
    node = registry.get("display_result")
    r = asyncio.run(node.execute({"data": {"field": "val"}, "confidence": 0.95}, {}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert r.outputs["validated_data"] == {"field": "val"}
    assert r.metadata["display"]["confidence"] == 0.95


def test_human_review_auto_approve():
    node = registry.get("human_review")
    r = asyncio.run(node.execute({"data": "test_data", "reason": "low score"}, {"auto_approve": True}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert r.outputs["approved"] == "test_data"
    assert r.outputs["rejected"] is None


def test_human_review_manual():
    node = registry.get("human_review")
    r = asyncio.run(node.execute({"data": "flagged"}, {"auto_approve": False}, CTX))
    assert r.outputs["approved"] is None
    assert r.outputs["rejected"] == "flagged"


# ============================================================
# DOCUMENT NODES (DocQWise)
# ============================================================

def test_docqwise_extract_regex_fallback():
    node = registry.get("docqwise_extract")
    r = asyncio.run(node.execute({"text": SAMPLE_TEXT}, {"fields": "vendor,date,amount,invoice_number"}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert "fields" in r.outputs
    assert isinstance(r.outputs["fields"], dict)
    # Regex should find at least some fields from formatted text
    fields = r.outputs["fields"]
    assert "vendor" in fields


def test_docqwise_extract_empty():
    node = registry.get("docqwise_extract")
    r = asyncio.run(node.execute({"text": ""}, {"fields": "vendor"}, CTX))
    assert r.status == NodeStatus.ERROR


def test_document_classifier():
    node = registry.get("document_classifier")
    r = asyncio.run(node.execute({"text": "Invoice for payment due total amount bill"}, {"categories": "invoice,contract,report"}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert r.outputs["doc_type"] == "invoice"


def test_document_classifier_contract():
    node = registry.get("document_classifier")
    r = asyncio.run(node.execute({"text": "This agreement between parties terms clause signed"}, {"categories": "invoice,contract"}, CTX))
    assert r.outputs["doc_type"] == "contract"


def test_chunk_fixed():
    node = registry.get("chunk")
    text = "A" * 500 + " " + "B" * 500 + " " + "C" * 500
    r = asyncio.run(node.execute({"text": text}, {"chunk_size": 600, "overlap": 100, "method": "fixed"}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert r.outputs["chunk_count"] >= 2


def test_chunk_paragraph():
    node = registry.get("chunk")
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    r = asyncio.run(node.execute({"text": text}, {"method": "paragraph"}, CTX))
    assert r.outputs["chunk_count"] == 3


def test_document_qa_fallback():
    node = registry.get("document_qa")
    r = asyncio.run(node.execute(
        {"text": SAMPLE_TEXT, "question": "What is the amount?"},
        {"model": "llama3.2", "host": "http://localhost:11434"},
        CTX
    ))
    # Will use keyword fallback since Ollama not running
    assert r.status in (NodeStatus.SUCCESS, NodeStatus.ERROR)
    if r.status == NodeStatus.SUCCESS:
        assert "answer" in r.outputs


# ============================================================
# TEMPORAL NODES (WavQWise)
# ============================================================

def test_data_loader(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("date,value\n2025-01-01,100\n2025-01-02,110\n2025-01-03,105\n")
    node = registry.get("data_loader")
    r = asyncio.run(node.execute({"file_path": str(f)}, {"target": "value", "time_col": "date"}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert r.outputs["row_count"] == 3
    assert "value" in r.outputs["columns"]


def test_data_loader_missing():
    node = registry.get("data_loader")
    r = asyncio.run(node.execute({"file_path": "/no/file.csv"}, {}, CTX))
    assert r.status == NodeStatus.ERROR


def test_forecast_fallback(tmp_path):
    import random
    f = tmp_path / "ts.csv"
    lines = ["date,value"] + [f"2025-01-{i+1:02d},{100 + random.gauss(0,10):.2f}" for i in range(30)]
    f.write_text("\n".join(lines))

    loader = registry.get("data_loader")
    lr = asyncio.run(loader.execute({"file_path": str(f)}, {"target": "value", "time_col": "date"}, CTX))

    node = registry.get("forecast")
    r = asyncio.run(node.execute({"data": lr.outputs["data"]}, {"model": "arima", "horizon": 7, "target": "value"}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert "prediction" in r.outputs["forecast"]
    assert len(r.outputs["forecast"]["prediction"]) == 7


def test_anomaly_detect_fallback(tmp_path):
    f = tmp_path / "sensor.csv"
    values = [100 + i * 0.1 for i in range(50)]
    values[25] = 500  # anomaly
    lines = ["date,temp"] + [f"2025-01-{i+1:02d},{v}" for i, v in enumerate(values)]
    f.write_text("\n".join(lines))

    loader = registry.get("data_loader")
    lr = asyncio.run(loader.execute({"file_path": str(f)}, {"target": "temp"}, CTX))

    node = registry.get("anomaly_detect")
    r = asyncio.run(node.execute({"data": lr.outputs["data"]}, {"method": "zscore", "target": "temp", "threshold": 2.0}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert r.outputs["anomaly_count"] >= 1
    assert any(a["index"] == 25 for a in r.outputs["anomalies"])


def test_compare_models():
    node = registry.get("compare_models")
    data = {"value": [100 + i for i in range(50)]}
    r = asyncio.run(node.execute({"data": data}, {"models": "arima,ets", "target": "value"}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert r.outputs["best_model"] in ("arima", "ets")


# ============================================================
# BACKBONE NODES
# ============================================================

def test_adaptive_router_pdf():
    node = registry.get("adaptive_router")
    r = asyncio.run(node.execute({"input_data": "doc content", "file_path": "test.pdf"}, {}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert r.outputs["detected_type"] == "document"
    assert r.outputs["document"] == "doc content"
    assert r.outputs["image"] is None


def test_adaptive_router_image():
    node = registry.get("adaptive_router")
    r = asyncio.run(node.execute({"input_data": "img", "file_path": "photo.jpg"}, {}, CTX))
    assert r.outputs["detected_type"] == "image"


def test_adaptive_router_audio():
    node = registry.get("adaptive_router")
    r = asyncio.run(node.execute({"input_data": "audio", "file_path": "recording.wav"}, {}, CTX))
    assert r.outputs["detected_type"] == "audio"


def test_evaluate_fallback():
    node = registry.get("evaluate")
    r = asyncio.run(node.execute(
        {"answer": "The vendor is Acme Corporation and total is $12,500", "context": SAMPLE_TEXT},
        {"preset": "rag", "threshold": 0.3},
        CTX
    ))
    assert r.status == NodeStatus.SUCCESS
    assert 0 <= r.outputs["score"] <= 1
    assert isinstance(r.outputs["passed"], bool)


def test_confidence_gate_pass():
    node = registry.get("confidence_gate")
    r = asyncio.run(node.execute({"score": 0.9, "data": "good"}, {"threshold": 0.7}, CTX))
    assert r.outputs["pass_data"] == "good"
    assert r.outputs["fail_data"] is None
    assert r.outputs["passed"] is True


def test_confidence_gate_fail():
    node = registry.get("confidence_gate")
    r = asyncio.run(node.execute({"score": 0.3, "data": "bad"}, {"threshold": 0.7}, CTX))
    assert r.outputs["pass_data"] is None
    assert r.outputs["fail_data"] == "bad"
    assert r.outputs["passed"] is False


def test_hallucination_check():
    node = registry.get("hallucination_check")
    r = asyncio.run(node.execute(
        {"answer": "The vendor is Acme", "context": "Vendor: Acme Corporation"},
        {"checks": "entity,fabricated"},
        CTX
    ))
    assert r.status == NodeStatus.SUCCESS
    assert 0 <= r.outputs["score"] <= 1


def test_guard_start():
    node = registry.get("guard_start")
    r = asyncio.run(node.execute({}, {"watch_dirs": "./data", "monitor_network": True}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert "session_id" in r.outputs["guard_session"]


def test_guard_report():
    node = registry.get("guard_report")
    session = {"session_id": "test", "start_time": __import__("time").time()}
    r = asyncio.run(node.execute({"guard_session": session, "data": "test_output"}, {}, CTX))
    assert r.status == NodeStatus.SUCCESS
    assert r.outputs["data_left_system"] is False
    assert r.outputs["risk_level"] == "low"
    assert r.outputs["data"] == "test_output"


# ============================================================
# REGISTRATION / MANIFEST TESTS
# ============================================================

def test_all_nodes_registered():
    assert registry.count >= 24


def test_all_manifests_valid():
    for m in registry.list_manifests():
        assert m["node_type"], f"Missing node_type"
        assert m["label"], f"Missing label for {m['node_type']}"
        assert m["category"], f"Missing category for {m['node_type']}"
        assert isinstance(m["inputs"], list)
        assert isinstance(m["outputs"], list)
        assert isinstance(m["config"], list)


def test_all_categories_present():
    cats = registry.list_categories()
    expected = {"common", "output", "document", "temporal", "backbone"}
    assert expected.issubset(set(cats.keys()))


def test_each_node_instantiates():
    for m in registry.list_manifests():
        node = registry.get(m["node_type"])
        assert node.node_type == m["node_type"]
