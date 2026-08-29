"""OCR Node — extract text from images/scanned PDFs."""
import os
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class OCRNode(BaseNode):
    node_type = "ocr"
    label = "OCR"
    category = "document"
    description = "Extract text from images or scanned documents"
    color = "#3b82f6"

    def define_inputs(self):
        return [Port("file_path", PortType.TEXT, "Path to image or PDF")]

    def define_outputs(self):
        return [
            Port("text", PortType.TEXT, "Extracted text"),
            Port("confidence", PortType.FLOAT, "OCR confidence"),
        ]

    def define_config(self):
        return [
            NodeConfig("engine", "OCR Engine", "select", default="tesseract", options=["tesseract", "easyocr", "paddleocr"]),
            NodeConfig("language", "Language", "string", default="eng"),
        ]

    async def execute(self, inputs, config, context):
        file_path = inputs.get("file_path", "")
        engine = config.get("engine", "tesseract")
        lang = config.get("language", "eng")

        if not file_path or not os.path.isfile(str(file_path)):
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message="File not found")

        try:
            if engine == "tesseract":
                import pytesseract
                from PIL import Image
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img, lang=lang)
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                confs = [int(c) for c in data["conf"] if int(c) > 0]
                confidence = sum(confs) / len(confs) / 100 if confs else 0.5
            elif engine == "easyocr":
                import easyocr
                reader = easyocr.Reader([lang[:2]])
                results = reader.readtext(str(file_path))
                text = " ".join([r[1] for r in results])
                confidence = sum(r[2] for r in results) / len(results) if results else 0.5
            else:
                text = "[OCR engine not available]"
                confidence = 0.0
        except ImportError as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Install {engine}: {e}")

        return NodeResult(
            outputs={"text": text, "confidence": confidence},
            message=f"OCR extracted {len(text)} chars (confidence: {confidence:.2f})",
        )
