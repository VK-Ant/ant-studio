"""Auto-register all Ant Studio nodes."""
from backend.core.node_registry import registry

def register_all_nodes():
    # ---- INPUT NODES ----
    from backend.nodes.common.file_input import FileInputNode
    from backend.nodes.common.text_input import TextInputNode
    from backend.nodes.common.database_input import DatabaseInputNode
    from backend.nodes.common.cloud_storage_input import CloudStorageInputNode
    from backend.nodes.common.url_input import URLInputNode
    from backend.nodes.common.ftp_input import FTPInputNode

    # ---- DOCUMENT NODES (DocQWise) ----
    from backend.nodes.document.pdf_loader import PDFLoaderNode
    from backend.nodes.document.ocr import OCRNode
    from backend.nodes.document.extract import DocQWiseExtractNode
    from backend.nodes.document.classifier import DocumentClassifierNode
    from backend.nodes.document.chunk import ChunkNode
    from backend.nodes.document.qa import DocumentQANode

    # ---- TEMPORAL NODES (WavQWise) ----
    from backend.nodes.temporal.data_loader import DataLoaderNode
    from backend.nodes.temporal.forecast import ForecastNode
    from backend.nodes.temporal.anomaly_detect import AnomalyDetectNode
    from backend.nodes.temporal.compare_models import CompareModelsNode

    # ---- BACKBONE NODES ----
    from backend.nodes.backbone.adaptive_router import AdaptiveRouterNode
    from backend.nodes.backbone.ollama_llm import OllamaLLMNode
    from backend.nodes.backbone.evaluate import EvaluateNode
    from backend.nodes.backbone.confidence_gate import ConfidenceGateNode
    from backend.nodes.backbone.hallucination_check import HallucinationCheckNode
    from backend.nodes.backbone.guard_start import GuardStartNode
    from backend.nodes.backbone.guard_report import GuardReportNode

    # ---- OUTPUT NODES ----
    from backend.nodes.common.export_csv import ExportCSVNode
    from backend.nodes.common.export_excel import ExportExcelNode
    from backend.nodes.common.export_json import ExportJSONNode
    from backend.nodes.common.display_result import DisplayResultNode
    from backend.nodes.common.human_review import HumanReviewNode
    from backend.nodes.common.save_to_database import SaveToDatabaseNode
    from backend.nodes.common.cloud_storage_output import CloudStorageOutputNode
    from backend.nodes.common.webhook_output import WebhookOutputNode

    for cls in [
        # Input (6)
        FileInputNode, TextInputNode, DatabaseInputNode,
        CloudStorageInputNode, URLInputNode, FTPInputNode,
        # Document (6)
        PDFLoaderNode, OCRNode, DocQWiseExtractNode,
        DocumentClassifierNode, ChunkNode, DocumentQANode,
        # Temporal (4)
        DataLoaderNode, ForecastNode, AnomalyDetectNode, CompareModelsNode,
        # Backbone (7)
        AdaptiveRouterNode, OllamaLLMNode, EvaluateNode,
        ConfidenceGateNode, HallucinationCheckNode,
        GuardStartNode, GuardReportNode,
        # Output (8)
        ExportCSVNode, ExportExcelNode, ExportJSONNode,
        DisplayResultNode, HumanReviewNode,
        SaveToDatabaseNode, CloudStorageOutputNode, WebhookOutputNode,
    ]:
        registry.register(cls)

    return registry.count
