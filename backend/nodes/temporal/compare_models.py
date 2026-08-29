"""Compare Models Node — benchmark multiple forecasting models."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class CompareModelsNode(BaseNode):
    node_type = "compare_models"
    label = "Compare Models"
    category = "temporal"
    description = "Benchmark multiple forecasting models and pick the best"
    color = "#14b8a6"

    def define_inputs(self):
        return [Port("data", PortType.DICT, "Time-series data")]

    def define_outputs(self):
        return [
            Port("ranking", PortType.LIST, "Models ranked by MAE"),
            Port("best_model", PortType.TEXT, "Best performing model name"),
            Port("comparison", PortType.DICT, "Full comparison results"),
        ]

    def define_config(self):
        return [
            NodeConfig("models", "Models to Compare", "string", default="arima,ets,holtwinters,moving_average"),
            NodeConfig("target", "Target Column", "string", default="value"),
            NodeConfig("horizon", "Test Horizon", "number", default=14),
        ]

    async def execute(self, inputs, config, context):
        data = inputs.get("data")
        if not data:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message="No data provided")

        models = [m.strip() for m in config.get("models", "").split(",")]
        target = config.get("target", "value")

        try:
            from wavqwise import WavqPipeline
            import pandas as pd
            df = pd.DataFrame(data)
            pipeline = WavqPipeline()
            pipeline.load(df, target=target)
            results = pipeline.compare_models(models=models, horizon=int(config.get("horizon", 14)))
            ranking = results.to_dict(orient="records") if hasattr(results, 'to_dict') else []
            best = ranking[0]["model"] if ranking else models[0]
            return NodeResult(
                outputs={"ranking": ranking, "best_model": best, "comparison": {"models": models}},
                message=f"Best model: {best}",
            )
        except ImportError:
            return NodeResult(
                outputs={"ranking": [{"model": m, "note": "install wavqwise"} for m in models],
                         "best_model": models[0], "comparison": {"models": models, "method": "fallback"}},
                message=f"Comparison stub — install wavqwise for real benchmarks",
            )
