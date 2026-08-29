"""Document Classifier Node."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class DocumentClassifierNode(BaseNode):
    node_type = "document_classifier"
    label = "Document Classifier"
    category = "document"
    description = "Classify document type (invoice, contract, report, etc.)"
    color = "#3b82f6"

    def define_inputs(self):
        return [Port("text", PortType.TEXT, "Document text")]

    def define_outputs(self):
        return [
            Port("doc_type", PortType.TEXT, "Detected document type"),
            Port("confidence", PortType.FLOAT, "Classification confidence"),
        ]

    def define_config(self):
        return [
            NodeConfig("categories", "Categories", "string", default="invoice,contract,report,letter,receipt,form"),
        ]

    async def execute(self, inputs, config, context):
        text = inputs.get("text", "").lower()
        categories = [c.strip() for c in config.get("categories", "").split(",")]

        try:
            from docqwise import DocQWise
            dq = DocQWise()
            result = dq.classify(text=text, categories=categories)
            return NodeResult(outputs={"doc_type": result.category, "confidence": result.confidence})
        except (ImportError, AttributeError):
            # Keyword-based fallback
            scores = {}
            keywords = {
                "invoice": ["invoice", "amount", "due", "total", "payment", "bill"],
                "contract": ["agreement", "parties", "terms", "clause", "signed"],
                "report": ["report", "summary", "analysis", "findings", "conclusion"],
                "letter": ["dear", "sincerely", "regards", "subject"],
                "receipt": ["receipt", "paid", "transaction", "subtotal"],
                "form": ["form", "fill", "applicant", "field", "checkbox"],
            }
            for cat in categories:
                kws = keywords.get(cat, [cat])
                scores[cat] = sum(1 for kw in kws if kw in text)

            if scores:
                best = max(scores, key=scores.get)
                total = sum(scores.values()) or 1
                return NodeResult(
                    outputs={"doc_type": best, "confidence": scores[best] / total},
                    message=f"Classified as {best} (keyword fallback)",
                )
            return NodeResult(outputs={"doc_type": "unknown", "confidence": 0.0})
