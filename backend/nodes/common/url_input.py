"""URL Input Node — download file from HTTP/HTTPS."""
import os
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class URLInputNode(BaseNode):
    node_type = "url_input"
    label = "URL Input"
    category = "input"
    description = "Download file from HTTP/HTTPS URL"
    color = "#6366f1"

    def define_inputs(self):
        return []

    def define_outputs(self):
        return [
            Port("file_path", PortType.TEXT, "Local path to downloaded file"),
            Port("content", PortType.TEXT, "Response text content"),
            Port("file_size", PortType.FLOAT, "Downloaded file size"),
        ]

    def define_config(self):
        return [
            NodeConfig("url", "URL", "string", default="https://example.com/data.csv"),
            NodeConfig("download_dir", "Download Directory", "string", default="./data/downloads"),
            NodeConfig("filename", "Save As (optional)", "string", default=""),
        ]

    async def execute(self, inputs, config, context):
        url = config.get("url", "")
        if not url:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message="No URL provided")

        download_dir = config.get("download_dir", "./data/downloads")
        os.makedirs(download_dir, exist_ok=True)
        filename = config.get("filename") or url.split("/")[-1].split("?")[0] or "download"
        local_path = os.path.join(download_dir, filename)

        try:
            import httpx
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                with open(local_path, "wb") as f:
                    f.write(resp.content)

                content = ""
                try:
                    content = resp.text
                except Exception:
                    pass

                return NodeResult(
                    outputs={"file_path": local_path, "content": content, "file_size": len(resp.content)},
                    message=f"Downloaded {filename} ({len(resp.content)} bytes)",
                )
        except Exception as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Download failed: {e}")
