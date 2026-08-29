"""Display Result Node — shows output in UI for user validation."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class DisplayResultNode(BaseNode):
    node_type = "display_result"
    label = "Display Result"
    category = "output"
    description = "Display results in the UI for visual validation"
    color = "#059669"

    def define_inputs(self):
        return [
            Port("data", PortType.ANY, "Data to display"),
            Port("confidence", PortType.FLOAT, "Confidence score", required=False),
            Port("sources", PortType.LIST, "Source references", required=False),
        ]

    def define_outputs(self):
        return [Port("validated_data", PortType.ANY, "Pass-through data for downstream nodes")]

    def define_config(self):
        return [NodeConfig("display_mode", "Display Mode", "select", default="table", options=["table", "json", "text", "cards"])]

    async def execute(self, inputs, config, context):
        data = inputs.get("data")
        confidence = inputs.get("confidence")
        sources = inputs.get("sources")

        display = {
            "data": data,
            "confidence": confidence,
            "sources": sources,
            "mode": config.get("display_mode", "table"),
        }

        return NodeResult(
            outputs={"validated_data": data},
            message=f"Displaying results (confidence: {confidence})" if confidence else "Displaying results",
            metadata={"display": display},
        )
