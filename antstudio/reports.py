"""Report generator — quality and audit reports saved alongside pipeline output.

Every pipeline run produces 2 report files:
  {output}_quality.json   — llmevalkit quality scores per step
  {output}_audit.json     — AntGuard privacy audit trail
"""
import json, os
from datetime import datetime
from pathlib import Path


def save_quality_report(quality_scores: dict, output_path: str,
                        pipeline_name: str = "", run_id: str = "") -> str:
    """Save llmevalkit quality scores as JSON."""
    report_path = _report_path(output_path, "quality")
    report = {
        "report_type": "quality",
        "generator": "llmevalkit",
        "version": "0.2.0",
        "pipeline": pipeline_name,
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_steps": len(quality_scores),
            "passed": sum(1 for s in quality_scores.values() if s.get("passed", False)),
            "failed": sum(1 for s in quality_scores.values() if not s.get("passed", True)),
            "average_score": round(
                sum(s.get("score", 0) for s in quality_scores.values()) /
                max(len(quality_scores), 1), 4
            ),
            "method": _dominant_method(quality_scores),
            "all_passed": all(s.get("passed", False) for s in quality_scores.values()) if quality_scores else True,
        },
        "steps": {
            name: {
                "score": s.get("score", 0),
                "passed": s.get("passed", False),
                "method": s.get("method", "unknown"),
            }
            for name, s in quality_scores.items()
        },
    }
    _write_json(report_path, report)
    return report_path


def save_audit_report(audit: dict, output_path: str,
                      pipeline_name: str = "", run_id: str = "") -> str:
    """Save AntGuard privacy audit as JSON."""
    report_path = _report_path(output_path, "audit")
    privacy = audit.get("privacy", {})
    report = {
        "report_type": "audit",
        "generator": "antguard",
        "version": "0.2.0",
        "pipeline": pipeline_name,
        "run_id": run_id,
        "timestamp": audit.get("timestamp", datetime.now().isoformat()),
        "command": audit.get("command", ""),
        "duration_seconds": audit.get("duration_seconds", 0),
        "platform": audit.get("platform", ""),
        "privacy": {
            "data_left_system": privacy.get("data_left_system", False),
            "risk_level": privacy.get("risk_level", "UNKNOWN"),
            "antguard_active": privacy.get("antguard_active", False),
            "verdict": "PASS" if not privacy.get("data_left_system", False) else "FAIL",
        },
        "quality_summary": {
            "all_passed": audit.get("passed", True),
            "scores": audit.get("quality_scores", {}),
        },
    }
    _write_json(report_path, report)
    return report_path


def save_reports(quality_scores: dict, audit: dict, output_path: str,
                 pipeline_name: str = "", run_id: str = "",
                 extra_info: dict = None, **kwargs) -> dict:
    """Save quality + audit reports. Returns dict of saved paths."""
    paths = {}
    paths["quality"] = save_quality_report(quality_scores, output_path, pipeline_name, run_id)
    paths["audit"] = save_audit_report(audit, output_path, pipeline_name, run_id)
    return paths


def _report_path(base_path: str, suffix: str) -> str:
    p = Path(base_path)
    return str(p.parent / f"{p.stem}_{suffix}.json")


def _dominant_method(scores: dict) -> str:
    methods = [s.get("method", "unknown") for s in scores.values()]
    if not methods:
        return "none"
    return max(set(methods), key=methods.count)


def _write_json(path: str, data: dict):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
