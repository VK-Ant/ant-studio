"""Text Input Node — user enters text manually."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class TextInputNode(BaseNode):
    node_type = "text_input"
    label = "Text Input"
    category = "common"
    description = "Enter text manually (question, prompt, or any text)"
    color = "#64748b"

    def define_inputs(self):
        return []

    def define_outputs(self):
        return [Port("text", PortType.TEXT, "User-entered text")]

    def define_config(self):
        return [
            NodeConfig("text", "Text", "text_area", default="What is the total amount?"),
            NodeConfig("label", "Label", "string", default="Question"),
        ]

    async def execute(self, inputs, config, context):
        text = config.get("text", "")
        return NodeResult(
            outputs={"text": text},
            message=f"{config.get('label', 'Text')}: {text[:50]}...",
        )
