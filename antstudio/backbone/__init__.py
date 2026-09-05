"""Backbone — runs on EVERY command automatically."""
import time, json, os, platform
from datetime import datetime
from pathlib import Path

HISTORY_DIR = Path.home() / ".antstudio"
HISTORY_FILE = HISTORY_DIR / "history.json"

class Backbone:
    def __init__(self, command: str):
        self.command = command
        self.start_time = time.time()
        self.quality_scores = {}
        self._guard = None
        self.guard_active = False

    def start(self):
        try:
            from antguard import Guard
            self._guard = Guard(detect_outbound=True, runtime=True)
            self._guard.__enter__()
            self.guard_active = True
        except ImportError:
            pass
        return self

    def evaluate(self, step: str, output, context: str = "") -> dict:
        text = str(output) if output else ""
        if not text or len(text) < 3:
            score = {"score": 0.0, "passed": False, "method": "empty"}
            self.quality_scores[step] = score
            return score
        try:
            from llmevalkit import Evaluator
            ev = Evaluator(provider="none", preset="rag", threshold=0.5)
            r = ev.evaluate(answer=text, context=context)
            score = {"score": r.overall_score, "passed": r.passed, "method": "llmevalkit"}
        except ImportError:
            s = min(len(text) / 200, 0.7)
            if context:
                cw = set(context.lower().split()[:30])
                ow = set(text.lower().split())
                s += len(cw & ow) / max(len(cw), 1) * 0.3
            s = min(round(s, 3), 1.0)
            score = {"score": s, "passed": s >= 0.5, "method": "fallback"}
        self.quality_scores[step] = score
        return score

    def route(self, path: str) -> str:
        try:
            from adaptive_intelligence import AdaptiveEngine
            return AdaptiveEngine().route(path)
        except ImportError:
            ext = Path(path).suffix.lower() if path else ""
            if ext in (".pdf", ".docx", ".doc", ".txt"):
                return "document"
            elif ext in (".csv", ".xlsx", ".parquet"):
                return "timeseries"
            elif ext in (".png", ".jpg", ".jpeg"):
                return "vision"
            elif ext in (".wav", ".mp3"):
                return "audio"
            return "document"

    def finish(self) -> dict:
        elapsed = time.time() - self.start_time
        data_left = False
        risk = "LOW"
        if self._guard and self.guard_active:
            try:
                self._guard.__exit__(None, None, None)
                data_left = self._guard.did_data_leave()
                risk = self._guard.risk_level().name
            except Exception:
                pass
        report = {
            "command": self.command, "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(elapsed, 2), "quality_scores": self.quality_scores,
            "privacy": {"data_left_system": data_left, "risk_level": risk, "antguard_active": self.guard_active},
            "platform": platform.system(),
            "passed": all(s.get("passed", False) for s in self.quality_scores.values()) if self.quality_scores else True,
        }
        self._save_history(report)
        return report

    def _save_history(self, report):
        try:
            HISTORY_DIR.mkdir(parents=True, exist_ok=True)
            history = json.loads(HISTORY_FILE.read_text()) if HISTORY_FILE.exists() else []
            report["id"] = len(history) + 1
            history.append(report)
            HISTORY_FILE.write_text(json.dumps(history[-500:], indent=2))
        except Exception:
            pass
