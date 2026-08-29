# Ant Studio — Testing Guide

## Quick Start

```bash
# Install test dependencies
pip install pytest

# Run all tests
PYTHONPATH=. python -m pytest tests/ -v

# Run by category
PYTHONPATH=. python -m pytest tests/test_core.py -v       # 16 framework tests
PYTHONPATH=. python -m pytest tests/test_nodes.py -v      # 35 node tests
PYTHONPATH=. python -m pytest tests/test_workflows.py -v  # 7 integration tests
```

## Test Categories

### test_core.py (16 tests)
Tests the platform foundation — no library dependencies needed.

- BaseNode: manifest generation, execution, port types
- NodeRegistry: register, get, list manifests, categories, unknown node error
- Workflow: from_dict, roundtrip, JSON file save/load
- WorkflowExecutor: simple pipeline, error handling (node fails → downstream skips), independent branches (error in one branch doesn't affect another)
- ResourceManager: model caching, LRU eviction, manual unload

### test_nodes.py (35 tests)
Tests each of the 24 nodes individually with mock/fallback data.

**Common nodes:**
- file_input: valid file, missing file, folder batch scan
- text_input: text entry
- export_csv: single dict, list of dicts
- export_json: any data
- display_result: data + confidence pass-through
- human_review: auto-approve mode, manual mode

**Document nodes (DocQWise):**
- docqwise_extract: regex fallback extraction, empty text error
- document_classifier: invoice detection, contract detection
- chunk: fixed-size, paragraph splitting
- document_qa: keyword fallback (Ollama unavailable)

**Temporal nodes (WavQWise):**
- data_loader: CSV loading, missing file error
- forecast: moving average fallback, 7-step horizon
- anomaly_detect: z-score fallback, detects injected anomaly
- compare_models: stub comparison

**Backbone nodes:**
- adaptive_router: PDF → document, JPG → image, WAV → audio
- evaluate: basic length+overlap fallback scoring
- confidence_gate: pass at 0.9, fail at 0.3
- hallucination_check: word overlap scoring
- guard_start: session creation
- guard_report: audit report generation, data_left_system=False

**Registration:**
- All 24+ nodes registered
- All manifests valid (have type, label, category, inputs, outputs)
- All categories present (common, output, document, temporal, backbone)
- Every registered node instantiates without error

### test_workflows.py (7 tests)
End-to-end integration tests — full pipelines from input to output.

- invoice_extraction: File → Extract → Evaluate (verifies vendor="TestCorp")
- forecasting: File → DataLoader → Forecast (verifies 7-step prediction)
- anomaly_detection: File → DataLoader → AnomalyDetect (verifies anomaly found)
- audit_pipeline: GuardStart → File → Extract → GuardReport (verifies data_left_system=False)
- confidence_routing: File → Extract → Evaluate → ConfidenceGate → HumanReview (verifies low-confidence fails gate)
- template_files: All template JSON files parse correctly
- save_reload: Workflow save → reload → identical

## Testing With Your Libraries

When you install your actual libraries, the fallbacks are replaced automatically.
Test the upgrade:

```bash
# Install your libraries
pip install docqwise llmevalkit antguard wavqwise

# Run tests — nodes will use real implementations instead of fallbacks
PYTHONPATH=. python -m pytest tests/ -v

# Test specific library integration
PYTHONPATH=. python -m pytest tests/test_nodes.py::test_docqwise_extract_regex_fallback -v
```

## Testing the API Server

```bash
# Start the server
uvicorn backend.main:app --reload

# Test endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/nodes | python -m json.tool
curl http://localhost:8000/api/templates
curl http://localhost:8000/api/resources

# Run a workflow via API
curl -X POST http://localhost:8000/api/workflows/run \
  -H "Content-Type: application/json" \
  -d @templates/invoice_extraction.json
```

## Testing CLI

```bash
PYTHONPATH=. python run_workflow.py templates/invoice_extraction.json
PYTHONPATH=. python run_workflow.py templates/sales_forecast.json
PYTHONPATH=. python run_workflow.py templates/sensor_anomaly.json
PYTHONPATH=. python run_workflow.py templates/document_qa.json
```
