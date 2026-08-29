"""Export JSON Node."""
import json, os
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class ExportJSONNode(BaseNode):
    node_type = "export_json"
    label = "Export JSON"
    category = "output"
    description = "Export data to JSON file"
    color = "#059669"

    def define_inputs(self):
        return [Port("data", PortType.ANY, "Data to export")]

    def define_outputs(self):
        return [Port("file_path", PortType.TEXT, "Path to exported JSON")]

    def define_config(self):
        return [NodeConfig("output_path", "Output Path", "string", default="./output/results.json")]

    async def execute(self, inputs, config, context):
        data = inputs.get("data")
        output_path = config.get("output_path", "./output/results.json")
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return NodeResult(outputs={"file_path": output_path}, message=f"Exported to {output_path}")
