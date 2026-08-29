"""Human Review Node — flags items for manual review."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class HumanReviewNode(BaseNode):
    node_type = "human_review"
    label = "Human Review"
    category = "output"
    description = "Flag items for manual review and approval"
    color = "#eab308"

    def define_inputs(self):
        return [
            Port("data", PortType.ANY, "Data to review"),
            Port("reason", PortType.TEXT, "Why review is needed", required=False),
        ]

    def define_outputs(self):
        return [
            Port("approved", PortType.ANY, "Approved data"),
            Port("rejected", PortType.ANY, "Rejected data"),
        ]

    def define_config(self):
        return [NodeConfig("auto_approve", "Auto-approve (for testing)", "boolean", default=True)]

    async def execute(self, inputs, config, context):
        data = inputs.get("data")
        reason = inputs.get("reason", "Low confidence")
        auto = config.get("auto_approve", True)

        if auto:
            return NodeResult(
                outputs={"approved": data, "rejected": None},
                message=f"Auto-approved ({reason})",
                metadata={"review_reason": reason, "auto": True},
            )
        return NodeResult(
            outputs={"approved": None, "rejected": data},
            message=f"Pending review: {reason}",
            metadata={"review_reason": reason, "auto": False, "pending": True},
        )
