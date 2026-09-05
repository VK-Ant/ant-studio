"""Time-series forecasting with pipeline tracking."""
import os
from typing import Optional
from antstudio.backbone import Backbone
from antstudio.pipeline import Pipeline

class Forecast:
    def __init__(self, predictions, model_used, quality, audit):
        self.predictions = predictions
        self.model_used = model_used
        self.count = len(predictions)
        self.quality = quality
        self.audit = audit
    def to_csv(self, path):
        import csv
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["step", "prediction"])
            for i, v in enumerate(self.predictions): w.writerow([i+1, v])
    def save_chart(self, path):
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10,4))
            plt.plot(self.predictions, color="#f97316", linewidth=2)
            plt.title(f"Forecast ({self.model_used}, {self.count} steps)")
            plt.xlabel("Step"); plt.ylabel("Value"); plt.tight_layout()
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            plt.savefig(path, dpi=150); plt.close()
        except ImportError: print("  pip install matplotlib")
    def __repr__(self): return f"Forecast({self.count} steps, model={self.model_used})"

def run(source, target="value", horizon=30, model="auto", output="", chart="", verbose=True, **kw):
    bb = Backbone(f"ts forecast {source}"); bb.start()
    pipe = Pipeline(f"Forecast: {source}"); pipe.start()

    if verbose: print(f"\n  Ant Studio v0.1.0 | WavQWise + llmevalkit + AntGuard\n")

    s1 = pipe.add_step("Load Data", "data_loader", {"source": source, "target": target}); s1.start()
    import pandas as pd
    try:
        df = pd.read_csv(source) if source.endswith(".csv") else pd.read_excel(source)
    except Exception as e:
        s1.fail(str(e)); pipe.finish()
        if verbose: pipe.print_status()
        return Forecast([], "none", {}, bb.finish())
    if target not in df.columns:
        s1.fail(f"Column '{target}' not found. Available: {list(df.columns)}"); pipe.finish()
        if verbose: pipe.print_status()
        return Forecast([], "none", {}, bb.finish())
    values = df[target].dropna().values.tolist()
    s1.succeed({"rows": len(values)}, f"{len(values)} rows")
    if verbose: print(f"  [1/3] Loading {'.' * 21} {len(values)} rows, target: {target}")

    s2 = pipe.add_step("Forecast", "wavqwise_forecast", {"model": model, "horizon": horizon}); s2.start()
    preds, model_used = _try_wavqwise(values, horizon, model)
    if not preds:
        preds, model_used = _fallback(values, horizon)
    s2.succeed({"steps": len(preds), "model": model_used}, f"{len(preds)} steps via {model_used}")
    if verbose: print(f"  [2/3] Forecasting ({model_used}) {'.'*(15-len(model_used))} {len(preds)} steps")

    s3 = pipe.add_step("Quality + Audit", "backbone", {}); s3.start()
    bb.evaluate("forecast", str(preds[:5]), str(values[-10:]))
    audit = bb.finish()
    dl = audit["privacy"]["data_left_system"]
    s3.succeed({"data_left": dl}, f"data_left: {'YES' if dl else 'NO'}")
    if verbose: print(f"  [3/3] Audit {'.' * 23} data_left: {'YES' if dl else 'NO'}")

    pipe.finish()
    result = Forecast(preds, model_used, bb.quality_scores, audit)
    if output: result.to_csv(output); verbose and print(f"\n  Saved: {output}")
    if chart: result.save_chart(chart); verbose and print(f"  Chart: {chart}")
    if verbose: pipe.print_status()
    return result

def _try_wavqwise(values, horizon, model):
    try:
        from wavqwise import WavQWise
        wq = WavQWise()
        r = wq.forecast(values, horizon=horizon, model=model)
        return r.predictions, r.model_used
    except ImportError: return [], ""

def _fallback(values, horizon):
    if len(values) < 3: return ([values[-1]]*horizon if values else [0]*horizon), "constant"
    w = min(7, len(values)); ma = sum(values[-w:])/w
    trend = (values[-1]-values[-w])/w
    return [round(ma+trend*(i+1), 4) for i in range(horizon)], "moving_average"
