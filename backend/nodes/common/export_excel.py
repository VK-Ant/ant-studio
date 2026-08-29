"""Export Excel Node."""
import os
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class ExportExcelNode(BaseNode):
    node_type = "export_excel"
    label = "Export Excel"
    category = "output"
    description = "Export structured data to Excel (.xlsx)"
    color = "#059669"

    def define_inputs(self):
        return [Port("data", PortType.ANY, "Data to export")]

    def define_outputs(self):
        return [Port("file_path", PortType.TEXT, "Path to exported Excel file")]

    def define_config(self):
        return [NodeConfig("output_path", "Output Path", "string", default="./output/results.xlsx")]

    async def execute(self, inputs, config, context):
        try:
            import openpyxl
        except ImportError:
            return NodeResult(outputs={}, message="pip install openpyxl required", status=__import__('backend.core.base_node', fromlist=['NodeStatus']).NodeStatus.ERROR)

        data = inputs.get("data")
        output_path = config.get("output_path", "./output/results.xlsx")
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        if isinstance(data, dict):
            rows = [data]
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            rows = data
        else:
            rows = [{"result": str(data)}]

        wb = openpyxl.Workbook()
        ws = wb.active
        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row.get(h, "") for h in headers])
        wb.save(output_path)

        return NodeResult(outputs={"file_path": output_path}, message=f"Exported {len(rows)} rows to {output_path}")
