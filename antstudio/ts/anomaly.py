"""Anomaly detection with pipeline tracking."""
import os, statistics
from antstudio.backbone import Backbone
from antstudio.pipeline import Pipeline

class Anomalies:
    def __init__(self, items, method, quality, audit):
        self.items = items; self.method = method; self.count = len(items)
        self.quality = quality; self.audit = audit
    def to_csv(self, path):
        import csv
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["index","value","score","severity"]); w.writeheader(); w.writerows(self.items)
    def __repr__(self): return f"Anomalies({self.count}, method={self.method})"

def run(source, target="value", method="zscore", threshold=2.0, output="", verbose=True, **kw):
    bb = Backbone(f"ts anomaly {source}"); bb.start()
    pipe = Pipeline(f"Anomaly Detection: {source}"); pipe.start()

    if verbose: print(f"\n  Ant Studio v0.2.0 | WavQWise + llmevalkit + AntGuard\n")

    s1 = pipe.add_step("Load Data", "data_loader", {"source": source, "target": target}); s1.start()
    import pandas as pd
    try:
        df = pd.read_csv(source) if source.endswith(".csv") else pd.read_excel(source)
    except Exception as e:
        s1.fail(str(e)); pipe.finish()
        if verbose: pipe.print_status()
        return Anomalies([], method, {}, bb.finish())
    if target not in df.columns:
        s1.fail(f"Column '{target}' not found"); pipe.finish()
        if verbose: pipe.print_status()
        return Anomalies([], method, {}, bb.finish())
    values = df[target].dropna().values.tolist()
    s1.succeed({"rows": len(values)}); 
    if verbose: print(f"  [1/3] Loading {'.' * 21} {len(values)} rows, target: {target}")

    s2 = pipe.add_step("Detect Anomalies", "wavqwise_anomaly", {"method": method, "threshold": threshold}); s2.start()
    anomalies = _try_wavqwise(values, method, threshold)
    if anomalies is None: anomalies = _fallback(values, method, threshold)
    s2.succeed({"count": len(anomalies)}, f"{len(anomalies)} anomalies")
    if verbose: print(f"  [2/3] Detecting ({method}) {'.'*(16-len(method))} {len(anomalies)} anomalies")

    s3 = pipe.add_step("Quality + Audit", "backbone", {}); s3.start()
    bb.evaluate("anomaly", str(anomalies[:3]), str(values[:20]))
    audit = bb.finish()
    dl = audit["privacy"]["data_left_system"]
    s3.succeed({"data_left": dl})
    if verbose: print(f"  [3/3] Audit {'.' * 23} data_left: {'YES' if dl else 'NO'}")

    pipe.finish()
    result = Anomalies(anomalies, method, bb.quality_scores, audit)
    if output:
        result.to_csv(output); verbose and print(f"\n  Saved: {output}")
        try:
            from antstudio.reports import save_reports
            extra = {"method": method, "threshold": threshold, "target": target,
                     "rows": len(values), "anomalies_found": len(anomalies)}
            report_paths = save_reports(
                bb.quality_scores, audit, output,
                pipeline_name=pipe.name, run_id=pipe.run_id, extra_info=extra
            )
            if verbose:
                for rtype, rpath in report_paths.items():
                    print(f"  Report ({rtype}): {rpath}")
        except Exception:
            pass
    if verbose: pipe.print_status()
    return result

def _try_wavqwise(values, method, threshold):
    try:
        from wavqwise import WavQWise
        return WavQWise().detect_anomalies(values, method=method, threshold=threshold)
    except ImportError: return None

def _fallback(values, method, threshold):
    if len(values) < 5: return []
    mean = statistics.mean(values); std = statistics.stdev(values) or 1
    anomalies = []
    for i, v in enumerate(values):
        z = abs(v - mean) / std
        if z > threshold:
            sev = "critical" if z > threshold*2 else "high" if z > threshold*1.5 else "medium"
            anomalies.append({"index": i, "value": round(v,4), "score": round(z,3), "severity": sev})
    return anomalies
