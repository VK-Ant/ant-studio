"""Time-series forecasting with pipeline tracking and visualization."""
import os
from typing import Optional, List
from antstudio.backbone import Backbone
from antstudio.pipeline import Pipeline

class Forecast:
    def __init__(self, predictions, model_used, quality, audit, history=None, dates=None, target_name="value"):
        self.predictions = predictions
        self.model_used = model_used
        self.count = len(predictions)
        self.quality = quality
        self.audit = audit
        self.history = history or []
        self.dates = dates or []
        self.target_name = target_name

    def to_csv(self, path):
        import csv
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["step", "prediction"])
            for i, v in enumerate(self.predictions): w.writerow([i+1, v])

    def save_chart(self, path, title="Sales Forecast", show_confidence=True):
        """Generate a production-grade forecast visualization.

        Produces a chart with:
        - Historical data (solid line)
        - Forecast predictions (dashed line, different color)
        - Confidence interval band (shaded area)
        - Clear legend and axis labels
        - Summary statistics annotation
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from datetime import datetime, timedelta

            fig, ax = plt.subplots(figsize=(14, 6))
            fig.patch.set_facecolor("#FAFAFA")
            ax.set_facecolor("#FAFAFA")

            hist = self.history
            preds = self.predictions
            n_hist = len(hist)
            n_pred = len(preds)

            # Build x-axis indices
            hist_x = list(range(n_hist))
            pred_x = list(range(n_hist, n_hist + n_pred))

            # If dates available, use them
            use_dates = False
            if self.dates and len(self.dates) == n_hist:
                try:
                    parsed = [datetime.strptime(str(d).strip(), "%Y-%m-%d") for d in self.dates]
                    delta = parsed[-1] - parsed[-2] if len(parsed) > 1 else timedelta(days=1)
                    pred_dates = [parsed[-1] + delta * (i+1) for i in range(n_pred)]
                    hist_x = parsed
                    pred_x = pred_dates
                    use_dates = True
                except Exception:
                    pass

            # Historical line
            ax.plot(hist_x, hist, color="#1E3A5F", linewidth=1.8, label="Historical", zorder=3)

            # Connection point
            if hist:
                bridge_x = [hist_x[-1], pred_x[0]]
                bridge_y = [hist[-1], preds[0]]
                ax.plot(bridge_x, bridge_y, color="#F97316", linewidth=2, linestyle="--", zorder=3)

            # Forecast line
            ax.plot(pred_x, preds, color="#F97316", linewidth=2.2, linestyle="--",
                    label=f"Forecast ({self.model_used})", zorder=3)

            # Confidence interval
            if show_confidence and n_pred > 1:
                import statistics
                if len(hist) >= 7:
                    residuals = []
                    w = min(7, len(hist))
                    for i in range(w, len(hist)):
                        ma = sum(hist[i-w:i]) / w
                        residuals.append(abs(hist[i] - ma))
                    base_std = statistics.mean(residuals) if residuals else 5.0
                else:
                    base_std = statistics.stdev(hist) * 0.3 if len(hist) > 2 else 5.0

                upper = []
                lower = []
                for i in range(n_pred):
                    spread = base_std * (1 + 0.08 * i)
                    upper.append(preds[i] + 1.96 * spread)
                    lower.append(preds[i] - 1.96 * spread)

                ax.fill_between(pred_x, lower, upper, alpha=0.15, color="#F97316",
                                label="95% Confidence", zorder=1)

            # Vertical divider
            if hist:
                ax.axvline(x=hist_x[-1], color="#999999", linewidth=0.8, linestyle=":", alpha=0.7, zorder=2)
                y_mid = (min(hist + preds) + max(hist + preds)) / 2
                ax.text(hist_x[-1], ax.get_ylim()[1] * 0.98, "  Forecast start",
                        fontsize=8, color="#666666", va="top", ha="left")

            # Summary box
            if hist and preds:
                last_val = hist[-1]
                last_pred = preds[-1]
                pct_change = ((last_pred - last_val) / last_val) * 100
                direction = "+" if pct_change > 0 else ""
                summary = (f"Last actual: {last_val:,.1f}\n"
                           f"End forecast: {last_pred:,.1f}\n"
                           f"Change: {direction}{pct_change:.1f}%\n"
                           f"Horizon: {n_pred} steps")
                props = dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="#CCCCCC", alpha=0.9)
                ax.text(0.02, 0.97, summary, transform=ax.transAxes, fontsize=8,
                        verticalalignment="top", bbox=props, family="monospace")

            # Styling
            ax.set_title(title, fontsize=14, fontweight="bold", color="#1E3A5F", pad=12)
            ax.set_xlabel("Date" if use_dates else "Time Step", fontsize=10, color="#555555")
            ax.set_ylabel(self.target_name.replace("_", " ").title(), fontsize=10, color="#555555")
            ax.legend(loc="upper left", framealpha=0.9, fontsize=9, bbox_to_anchor=(0.0, 0.78))
            ax.grid(True, alpha=0.3, linewidth=0.5)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#CCCCCC")
            ax.spines["bottom"].set_color("#CCCCCC")

            if use_dates:
                fig.autofmt_xdate()
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

            # Branding
            fig.text(0.99, 0.01, "Ant Studio", fontsize=7, color="#AAAAAA", ha="right", va="bottom")

            plt.tight_layout()
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            plt.savefig(path, dpi=150, bbox_inches="tight", facecolor="#FAFAFA")
            plt.close()
        except ImportError:
            print("  pip install matplotlib")

    def __repr__(self): return f"Forecast({self.count} steps, model={self.model_used})"

def run(source, target="value", horizon=30, model="auto", output="", chart="", verbose=True, **kw):
    bb = Backbone(f"ts forecast {source}"); bb.start()
    pipe = Pipeline(f"Forecast: {source}"); pipe.start()

    if verbose: print(f"\n  Ant Studio v0.2.0 | WavQWise + llmevalkit + AntGuard\n")

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

    # Extract date column if present
    dates = []
    for col in ["date", "Date", "DATE", "timestamp", "Timestamp", "ds", "time", "Time"]:
        if col in df.columns:
            dates = df[col].dropna().values.tolist()
            break

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
    result = Forecast(preds, model_used, bb.quality_scores, audit,
                      history=values, dates=dates, target_name=target)

    if output: result.to_csv(output); verbose and print(f"\n  Saved: {output}")

    # Auto-generate chart if not specified but chart is wanted
    if chart:
        result.save_chart(chart)
        verbose and print(f"  Chart: {chart}")
    elif output:
        # Auto-save chart alongside output
        chart_path = output.rsplit(".", 1)[0] + "_forecast.png"
        result.save_chart(chart_path)
        verbose and print(f"  Chart: {chart_path}")

    # Save quality + audit reports alongside output
    if output:
        try:
            from antstudio.reports import save_reports
            extra = {"model": model_used, "horizon": horizon, "target": target,
                     "history_rows": len(values), "predictions": len(preds)}
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
