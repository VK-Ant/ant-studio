"""File Input Node — accepts file upload or path."""
import os
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class FileInputNode(BaseNode):
    node_type = "file_input"
    label = "File Input"
    category = "common"
    description = "Load a file from disk or upload"
    color = "#64748b"

    def define_inputs(self):
        return []

    def define_outputs(self):
        return [
            Port("file_path", PortType.TEXT, "Path to the file"),
            Port("file_name", PortType.TEXT, "File name"),
            Port("file_size", PortType.FLOAT, "File size in bytes"),
            Port("content", PortType.TEXT, "File content (text files only)"),
        ]

    def define_config(self):
        return [
            NodeConfig("path", "File Path", "string", default=""),
            NodeConfig("folder", "Folder Path (batch)", "string", default=""),
            NodeConfig("extensions", "File Extensions", "string", default=".pdf,.docx,.xlsx,.txt,.png,.jpg"),
        ]

    async def execute(self, inputs, config, context):
        path = config.get("path", "")
        folder = config.get("folder", "")
        exts = [e.strip() for e in config.get("extensions", "").split(",")]

        if folder and os.path.isdir(folder):
            files = []
            for root, _, filenames in os.walk(folder):
                for fn in filenames:
                    if any(fn.lower().endswith(ext) for ext in exts):
                        files.append(os.path.join(root, fn))
            if not files:
                return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"No matching files in {folder}")
            return NodeResult(
                outputs={"file_path": files, "file_name": [os.path.basename(f) for f in files], "file_size": sum(os.path.getsize(f) for f in files)},
                message=f"Found {len(files)} files",
            )
        elif path and os.path.isfile(path):
            # Read content for text files
            content_text = ""
            try:
                if any(path.lower().endswith(e) for e in [".txt", ".md", ".csv", ".json", ".xml", ".html"]):
                    with open(path, "r", errors="ignore") as f:
                        content_text = f.read()
            except Exception:
                pass
            return NodeResult(
                outputs={"file_path": path, "file_name": os.path.basename(path), "file_size": os.path.getsize(path), "content": content_text},
                message=f"Loaded {os.path.basename(path)}",
            )
        else:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"File not found: {path or folder}")
