"""Evaluate Node — llmevalkit quality scoring."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class EvaluateNode(BaseNode):
    node_type = "evaluate"
    label = "Evaluate"
    category = "backbone"
    description = "Score output quality using llmevalkit (78 metrics)"
    color = "#f97316"

    def define_inputs(self):
        return [
            Port("answer", PortType.TEXT, "Output to evaluate"),
            Port("context", PortType.TEXT, "Source context", required=False),
            Port("reference", PortType.TEXT, "Ground truth", required=False),
        ]

    def define_outputs(self):
        return [
            Port("score", PortType.FLOAT, "Overall quality score (0-1)"),
            Port("passed", PortType.BOOL, "Above threshold?"),
            Port("details", PortType.DICT, "Per-metric breakdown"),
        ]

    def define_config(self):
        return [
            NodeConfig("preset", "Evaluation Preset", "select", default="rag",
                       options=["rag", "chatbot", "safety", "hallucination", "hallucination_quick",
                                "doceval", "groundtruth", "redteam", "production", "math"]),
            NodeConfig("threshold", "Pass Threshold", "number", default=0.5, min_val=0, max_val=1),
        ]

    async def execute(self, inputs, config, context):
        answer = inputs.get("answer", "")
        ctx = inputs.get("context", "")
        ref = inputs.get("reference", "")
        preset = config.get("preset", "rag")
        threshold = config.get("threshold", 0.5)

        if isinstance(answer, dict):
            answer = str(answer)

        try:
            from llmevalkit import Evaluator
            e = Evaluator(provider="none", preset=preset, threshold=threshold)
            result = e.evaluate(answer=answer, context=ctx, reference=ref)
            return NodeResult(outputs={
                "score": result.overall_score,
                "passed": result.passed,
                "details": {k: v.score for k, v in result.metrics.items()},
            }, message=f"Score: {result.overall_score:.2f} ({'PASS' if result.passed else 'FAIL'})")
        except ImportError:
            # Fallback: basic length + keyword scoring
            score = min(len(answer) / 200, 1.0) * 0.7
            if ctx and any(w in answer.lower() for w in ctx.lower().split()[:10]):
                score += 0.3
            score = min(score, 1.0)
            passed = score >= threshold
            return NodeResult(outputs={
                "score": round(score, 3),
                "passed": passed,
                "details": {"length_score": min(len(answer) / 200, 1.0), "method": "basic_fallback"},
            }, message=f"Score: {score:.2f} ({'PASS' if passed else 'FAIL'}) (install llmevalkit for 78 metrics)")
