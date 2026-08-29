"""Chunk Node — split document into chunks."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class ChunkNode(BaseNode):
    node_type = "chunk"
    label = "Chunk"
    category = "document"
    description = "Split document text into chunks for processing"
    color = "#3b82f6"

    def define_inputs(self):
        return [Port("text", PortType.TEXT, "Document text")]

    def define_outputs(self):
        return [
            Port("chunks", PortType.LIST, "List of text chunks"),
            Port("chunk_count", PortType.FLOAT, "Number of chunks"),
        ]

    def define_config(self):
        return [
            NodeConfig("chunk_size", "Chunk Size (chars)", "number", default=1000),
            NodeConfig("overlap", "Overlap (chars)", "number", default=200),
            NodeConfig("method", "Method", "select", default="fixed", options=["fixed", "sentence", "paragraph"]),
        ]

    async def execute(self, inputs, config, context):
        text = inputs.get("text", "")
        size = int(config.get("chunk_size", 1000))
        overlap = int(config.get("overlap", 200))
        method = config.get("method", "fixed")

        if method == "paragraph":
            chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
        elif method == "sentence":
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text)
            chunks, current = [], ""
            for s in sentences:
                if len(current) + len(s) > size and current:
                    chunks.append(current.strip())
                    current = current[-overlap:] if overlap else ""
                current += " " + s
            if current.strip():
                chunks.append(current.strip())
        else:
            chunks = []
            for i in range(0, len(text), size - overlap):
                chunks.append(text[i:i + size])
                if i + size >= len(text):
                    break

        return NodeResult(
            outputs={"chunks": chunks, "chunk_count": len(chunks)},
            message=f"Split into {len(chunks)} chunks ({method})",
        )
