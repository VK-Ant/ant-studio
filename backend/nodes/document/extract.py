"""DocQWise Extract Node — structured field extraction from documents."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class DocQWiseExtractNode(BaseNode):
    node_type = "docqwise_extract"
    label = "DocQWise Extract"
    category = "document"
    description = "Extract structured fields from documents using DocQWise"
    color = "#8b5cf6"

    def define_inputs(self):
        return [Port("text", PortType.TEXT, "Document text")]

    def define_outputs(self):
        return [
            Port("fields", PortType.DICT, "Extracted fields"),
            Port("confidence", PortType.FLOAT, "Extraction confidence"),
            Port("sources", PortType.LIST, "Source references"),
            Port("raw_result", PortType.DICT, "Full extraction result"),
        ]

    def define_config(self):
        return [
            NodeConfig("fields", "Fields to Extract", "string", default="vendor,date,amount,invoice_number"),
            NodeConfig("model", "Extraction Model", "select", default="default", options=["default", "accurate", "fast"]),
            NodeConfig("use_llm", "Use LLM for extraction", "boolean", default=True),
        ]

    async def execute(self, inputs, config, context):
        text = inputs.get("text", "")
        if not text:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message="No text provided")

        field_list = [f.strip() for f in config.get("fields", "").split(",") if f.strip()]
        model = config.get("model", "default")
        use_llm = config.get("use_llm", True)

        try:
            from docqwise import DocQWise
            dq = DocQWise(model=model)
            result = dq.extract(text=text, fields=field_list)
            return NodeResult(
                outputs={
                    "fields": result.fields if hasattr(result, 'fields') else {},
                    "confidence": result.confidence if hasattr(result, 'confidence') else 0.0,
                    "sources": result.sources if hasattr(result, 'sources') else [],
                    "raw_result": result.__dict__ if hasattr(result, '__dict__') else {},
                },
                message=f"Extracted {len(field_list)} fields",
            )
        except ImportError:
            # Fallback: basic regex-based extraction for demo
            import re
            fields = {}
            for field_name in field_list:
                pattern = rf"(?i){field_name}\s*[:\-=]\s*(.+?)(?:\n|$)"
                match = re.search(pattern, text)
                fields[field_name] = match.group(1).strip() if match else ""

            filled = sum(1 for v in fields.values() if v)
            confidence = filled / len(field_list) if field_list else 0.0

            return NodeResult(
                outputs={
                    "fields": fields,
                    "confidence": confidence,
                    "sources": [{"method": "regex_fallback"}],
                    "raw_result": {"fields": fields, "method": "regex_fallback"},
                },
                message=f"Extracted {filled}/{len(field_list)} fields (regex fallback, install docqwise for full accuracy)",
            )
