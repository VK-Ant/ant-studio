"""Data Loader Node — load time-series from CSV/Excel/Parquet."""
import os
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class DataLoaderNode(BaseNode):
    node_type = "data_loader"
    label = "Data Loader"
    category = "temporal"
    description = "Load time-series data from CSV, Excel, or Parquet files"
    color = "#14b8a6"

    def define_inputs(self):
        return [Port("file_path", PortType.TEXT, "Path to data file")]

    def define_outputs(self):
        return [
            Port("data", PortType.DICT, "Loaded DataFrame as dict"),
            Port("columns", PortType.LIST, "Column names"),
            Port("row_count", PortType.FLOAT, "Number of rows"),
            Port("preview", PortType.TEXT, "First 5 rows preview"),
        ]

    def define_config(self):
        return [
            NodeConfig("target", "Target Column", "string", default="value"),
            NodeConfig("time_col", "Time Column", "string", default="date"),
            NodeConfig("format", "File Format", "select", default="auto", options=["auto", "csv", "excel", "parquet"]),
        ]

    async def execute(self, inputs, config, context):
        file_path = inputs.get("file_path", "")
        if isinstance(file_path, list):
            file_path = file_path[0]
        if not file_path or not os.path.isfile(str(file_path)):
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"File not found: {file_path}")

        try:
            import pandas as pd
            fmt = config.get("format", "auto")
            ext = str(file_path).rsplit(".", 1)[-1].lower()

            if fmt == "excel" or ext in ("xlsx", "xls"):
                df = pd.read_excel(file_path)
            elif fmt == "parquet" or ext == "parquet":
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)

            time_col = config.get("time_col", "date")
            if time_col in df.columns:
                df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
                df = df.sort_values(time_col)

            preview = df.head().to_string()
            return NodeResult(
                outputs={
                    "data": df.to_dict(orient="list"),
                    "columns": list(df.columns),
                    "row_count": len(df),
                    "preview": preview,
                },
                message=f"Loaded {len(df)} rows, {len(df.columns)} columns",
            )
        except ImportError:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message="pip install pandas required")
