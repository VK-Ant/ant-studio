"""Adaptive Router Node — routes input to correct pipeline."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class AdaptiveRouterNode(BaseNode):
    node_type = "adaptive_router"
    label = "Adaptive Router"
    category = "backbone"
    description = "Route input to the correct processing pipeline based on type"
    color = "#f97316"

    def define_inputs(self):
        return [
            Port("input_data", PortType.ANY, "Data to route"),
            Port("file_path", PortType.TEXT, "File path for type detection", required=False),
        ]

    def define_outputs(self):
        return [
            Port("document", PortType.ANY, "Document pipeline output"),
            Port("image", PortType.ANY, "Image pipeline output"),
            Port("audio", PortType.ANY, "Audio pipeline output"),
            Port("timeseries", PortType.ANY, "Time-series pipeline output"),
            Port("detected_type", PortType.TEXT, "Detected input type"),
        ]

    async def execute(self, inputs, config, context):
        data = inputs.get("input_data")
        file_path = inputs.get("file_path", "")

        detected = "unknown"
        if isinstance(file_path, str):
            ext = file_path.lower().rsplit(".", 1)[-1] if "." in file_path else ""
            if ext in ("pdf", "docx", "doc", "txt", "xlsx", "csv"):
                detected = "document"
            elif ext in ("png", "jpg", "jpeg", "bmp", "tiff", "webp"):
                detected = "image"
            elif ext in ("wav", "mp3", "flac", "ogg", "m4a"):
                detected = "audio"

        outputs = {"document": None, "image": None, "audio": None, "timeseries": None, "detected_type": detected}
        if detected in outputs:
            outputs[detected] = data

        return NodeResult(outputs=outputs, message=f"Routed to: {detected}")
