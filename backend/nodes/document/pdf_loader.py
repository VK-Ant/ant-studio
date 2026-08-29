"""PDF Loader Node — parse PDF to text + pages."""
import os
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class PDFLoaderNode(BaseNode):
    node_type = "pdf_loader"
    label = "PDF Loader"
    category = "document"
    description = "Load and parse PDF documents to text"
    color = "#3b82f6"

    def define_inputs(self):
        return [Port("file_path", PortType.TEXT, "Path to PDF file")]

    def define_outputs(self):
        return [
            Port("text", PortType.TEXT, "Extracted text"),
            Port("pages", PortType.LIST, "List of page texts"),
            Port("page_count", PortType.FLOAT, "Number of pages"),
            Port("metadata", PortType.DICT, "File metadata"),
        ]

    def define_config(self):
        return [
            NodeConfig("engine", "PDF Engine", "select", default="pymupdf", options=["pymupdf", "pdfplumber", "pypdf2"]),
        ]

    async def execute(self, inputs, config, context):
        file_path = inputs.get("file_path", "")
        if isinstance(file_path, list):
            file_path = file_path[0]

        if not file_path or not os.path.isfile(file_path):
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"PDF not found: {file_path}")

        engine = config.get("engine", "pymupdf")
        pages = []

        try:
            if engine == "pymupdf":
                import fitz
                doc = fitz.open(file_path)
                pages = [page.get_text() for page in doc]
                doc.close()
            elif engine == "pdfplumber":
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    pages = [p.extract_text() or "" for p in pdf.pages]
            else:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                pages = [p.extract_text() or "" for p in reader.pages]
        except ImportError as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Install {engine}: {e}")

        full_text = "\n\n".join(pages)
        return NodeResult(
            outputs={
                "text": full_text,
                "pages": pages,
                "page_count": len(pages),
                "metadata": {"file": os.path.basename(file_path), "engine": engine},
            },
            message=f"Loaded {len(pages)} pages from {os.path.basename(file_path)}",
        )
