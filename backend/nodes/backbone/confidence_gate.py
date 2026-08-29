"""Confidence Gate Node — route based on threshold."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class ConfidenceGateNode(BaseNode):
    node_type = "confidence_gate"
    label = "Confidence Gate"
    category = "backbone"
    description = "Route data based on confidence score threshold"
    color = "#eab308"

    def define_inputs(self):
        return [
            Port("score", PortType.FLOAT, "Confidence score to check"),
            Port("data", PortType.ANY, "Data to pass through"),
        ]

    def define_outputs(self):
        return [
            Port("pass_data", PortType.ANY, "Data when score >= threshold"),
            Port("fail_data", PortType.ANY, "Data when score < threshold"),
            Port("passed", PortType.BOOL, "Whether the gate passed"),
        ]

    def define_config(self):
        return [NodeConfig("threshold", "Threshold", "number", default=0.7, min_val=0, max_val=1)]

    async def execute(self, inputs, config, context):
        score = float(inputs.get("score", 0))
        data = inputs.get("data")
        threshold = float(config.get("threshold", 0.7))

        if score >= threshold:
            return NodeResult(
                outputs={"pass_data": data, "fail_data": None, "passed": True},
                message=f"PASS: {score:.2f} >= {threshold}",
            )
        return NodeResult(
            outputs={"pass_data": None, "fail_data": data, "passed": False},
            message=f"FAIL: {score:.2f} < {threshold}",
        )
