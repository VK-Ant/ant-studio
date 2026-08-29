"""Hallucination Check Node — detect fabricated content."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class HallucinationCheckNode(BaseNode):
    node_type = "hallucination_check"
    label = "Hallucination Check"
    category = "backbone"
    description = "Detect hallucinated/fabricated content in extraction results"
    color = "#ef4444"

    def define_inputs(self):
        return [
            Port("answer", PortType.TEXT, "Generated/extracted text"),
            Port("context", PortType.TEXT, "Source document text"),
        ]

    def define_outputs(self):
        return [
            Port("score", PortType.FLOAT, "Hallucination score (1=clean, 0=hallucinated)"),
            Port("issues", PortType.LIST, "Detected issues"),
        ]

    def define_config(self):
        return [
            NodeConfig("checks", "Checks", "string", default="entity,numeric,fabricated"),
        ]

    async def execute(self, inputs, config, context):
        answer = str(inputs.get("answer", ""))
        ctx = str(inputs.get("context", ""))

        try:
            from llmevalkit.hallucination import EntityHallucination, NumericHallucination, FabricatedInfo
            checks = config.get("checks", "entity,numeric,fabricated").split(",")
            metrics = []
            if "entity" in checks: metrics.append(EntityHallucination())
            if "numeric" in checks: metrics.append(NumericHallucination())
            if "fabricated" in checks: metrics.append(FabricatedInfo())

            issues = []
            scores = []
            for m in metrics:
                r = m.evaluate(answer=answer, context=ctx)
                scores.append(r.score)
                if r.score < 0.8:
                    issues.append({"metric": r.name, "score": r.score, "reason": r.reason})

            avg = sum(scores) / len(scores) if scores else 1.0
            return NodeResult(outputs={"score": avg, "issues": issues},
                              message=f"Hallucination score: {avg:.2f} ({len(issues)} issues)")
        except ImportError:
            # Fallback: basic word overlap check
            answer_words = set(answer.lower().split())
            ctx_words = set(ctx.lower().split())
            overlap = len(answer_words & ctx_words) / len(answer_words) if answer_words else 1.0
            return NodeResult(outputs={"score": round(overlap, 3), "issues": []},
                              message=f"Overlap: {overlap:.2f} (install llmevalkit for deep check)")
