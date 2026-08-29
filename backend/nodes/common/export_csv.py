"""Export CSV Node."""
import csv, os, json
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class ExportCSVNode(BaseNode):
    node_type = "export_csv"
    label = "Export CSV"
    category = "output"
    description = "Export structured data to CSV file"
    color = "#059669"

    def define_inputs(self):
        return [Port("data", PortType.ANY, "Data to export")]

    def define_outputs(self):
        return [Port("file_path", PortType.TEXT, "Path to exported CSV")]

    def define_config(self):
        return [NodeConfig("output_path", "Output Path", "string", default="./output/results.csv")]

    async def execute(self, inputs, config, context):
        data = inputs.get("data")
        output_path = config.get("output_path", "./output/results.csv")
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        if isinstance(data, dict):
            rows = [data]
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            rows = data
        else:
            rows = [{"result": str(data)}]

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        return NodeResult(outputs={"file_path": output_path}, message=f"Exported {len(rows)} rows to {output_path}")
