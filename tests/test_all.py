"""Ant Studio tests."""
import os, sys, tempfile, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "samples")

def test_doc_extract_single():
    from antstudio.doc.extract import run
    r = run(source=os.path.join(SAMPLES, "sample_invoice.txt"), fields=["vendor", "amount"], verbose=False)
    assert r.count == 1
    assert r.rows[0].get("vendor")

def test_doc_extract_folder():
    from antstudio.doc.extract import run
    r = run(source=SAMPLES, fields=["vendor"], verbose=False, extensions=".txt")
    assert r.count >= 1

def test_doc_extract_csv_output():
    from antstudio.doc.extract import run
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name
    try:
        r = run(source=os.path.join(SAMPLES, "sample_invoice.txt"), fields=["vendor", "amount"],
                output=path, verbose=False)
        assert os.path.exists(path)
        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) >= 2
    finally:
        os.unlink(path)

def test_ts_forecast():
    from antstudio.ts.forecast import run
    r = run(source=os.path.join(SAMPLES, "daily_sales.csv"), target="value", horizon=7, verbose=False)
    assert r.count == 7
    assert len(r.predictions) == 7

def test_ts_anomaly():
    from antstudio.ts.anomaly import run
    r = run(source=os.path.join(SAMPLES, "sensor_readings.csv"), target="temperature", verbose=False)
    assert r.count > 0

def test_backbone_auto_runs():
    from antstudio.doc.extract import run
    r = run(source=os.path.join(SAMPLES, "sample_invoice.txt"), fields=["vendor"], verbose=False)
    assert r.audit.get("privacy", {}).get("data_left_system") == False

def test_results_save_json():
    from antstudio.io.writer import Results
    r = Results([{"name": "test", "value": 123}])
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        r.to_json(path)
        assert os.path.exists(path)
        import json
        data = json.loads(open(path).read())
        assert len(data) == 1
    finally:
        os.unlink(path)

def test_history_saved():
    from pathlib import Path
    import json
    hist = Path.home() / ".antstudio" / "history.json"
    if hist.exists():
        data = json.loads(hist.read_text())
        assert isinstance(data, list)

def test_ollama_list():
    from antstudio.llm.ollama import list_models
    result = list_models()
    assert isinstance(result, list)

def test_reader_missing_file():
    from antstudio.io.reader import read_input
    r = read_input(source="/nonexistent/path.pdf")
    assert r == []
