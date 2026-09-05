"""Ant Studio Pipeline Tracker — Kubeflow-style flow visualization UI."""
import json, os, sys
from pathlib import Path
from flask import Flask, jsonify, send_from_directory

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__, static_folder="static")
RUNS_DIR = Path.home() / ".antstudio" / "runs"
HISTORY_FILE = Path.home() / ".antstudio" / "history.json"


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/runs")
def api_runs():
    runs = []
    if RUNS_DIR.exists():
        for f in sorted(RUNS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)[:50]:
            try:
                runs.append(json.loads(f.read_text()))
            except Exception:
                pass
    return jsonify(runs)


@app.route("/api/runs/<run_id>")
def api_run_detail(run_id):
    if RUNS_DIR.exists():
        path = RUNS_DIR / f"{run_id}.json"
        if path.exists():
            return jsonify(json.loads(path.read_text()))
        for f in RUNS_DIR.glob(f"{run_id}*.json"):
            return jsonify(json.loads(f.read_text()))
    return jsonify({"error": "not found"}), 404


@app.route("/api/history")
def api_history():
    if HISTORY_FILE.exists():
        return jsonify(json.loads(HISTORY_FILE.read_text())[-50:])
    return jsonify([])


@app.route("/api/demo-run", methods=["POST"])
def demo_run():
    """Run the sample forecast pipeline and return the run data."""
    try:
        from antstudio.ts.forecast import run
        samples = Path(__file__).parent.parent / "data" / "samples" / "daily_sales.csv"
        if not samples.exists():
            return jsonify({"error": "sample data not found"}), 404
        r = run(source=str(samples), target="value", horizon=14,
                output="/output/demo_forecast.csv", chart="/output/demo_forecast.png",
                verbose=False)
        # Return the latest run
        runs = []
        if RUNS_DIR.exists():
            for f in sorted(RUNS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)[:1]:
                runs.append(json.loads(f.read_text()))
        return jsonify(runs[0] if runs else {"status": "complete", "predictions": len(r.predictions)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=8501, debug=True)
