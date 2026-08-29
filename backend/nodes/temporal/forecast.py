"""Forecast Node — run WavQWise forecasting models."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class ForecastNode(BaseNode):
    node_type = "forecast"
    label = "Forecast"
    category = "temporal"
    description = "Run time-series forecasting using WavQWise (33 models)"
    color = "#14b8a6"

    def define_inputs(self):
        return [Port("data", PortType.DICT, "Time-series data (from Data Loader)")]

    def define_outputs(self):
        return [
            Port("forecast", PortType.DICT, "Forecast results with predictions + confidence intervals"),
            Port("metrics", PortType.DICT, "Evaluation metrics (MAE, RMSE, MAPE)"),
            Port("model_used", PortType.TEXT, "Which model was used"),
        ]

    def define_config(self):
        return [
            NodeConfig("model", "Model", "select", default="arima",
                       options=["arima", "auto_arima", "ets", "holtwinters", "theta",
                                "xgboost", "lightgbm", "random_forest", "ridge",
                                "moving_average", "ema", "naive", "seasonal_naive",
                                "neuralprophet", "chronos", "auto"]),
            NodeConfig("horizon", "Forecast Horizon", "number", default=30),
            NodeConfig("target", "Target Column", "string", default="value"),
            NodeConfig("time_col", "Time Column", "string", default="date"),
        ]

    async def execute(self, inputs, config, context):
        data = inputs.get("data")
        if not data:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message="No data provided")

        model = config.get("model", "arima")
        horizon = int(config.get("horizon", 30))
        target = config.get("target", "value")
        time_col = config.get("time_col", "date")

        try:
            from wavqwise import WavqPipeline
            import pandas as pd

            df = pd.DataFrame(data)
            pipeline = WavqPipeline()
            pipeline.load(df, target=target, time=time_col)
            result = pipeline.forecast(horizon=horizon, model=model)

            return NodeResult(
                outputs={
                    "forecast": result.forecast.to_dict(orient="list") if hasattr(result, 'forecast') else {},
                    "metrics": result.metrics if hasattr(result, 'metrics') else {},
                    "model_used": model,
                },
                message=f"Forecast {horizon} steps using {model}",
            )
        except ImportError:
            # Fallback: simple moving average forecast
            import statistics
            values = data.get(target, [])
            if not values or not isinstance(values, list):
                return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Column '{target}' not found")

            recent = [v for v in values[-30:] if isinstance(v, (int, float))]
            if not recent:
                return NodeResult(outputs={}, status=NodeStatus.ERROR, message="No numeric values found")

            avg = statistics.mean(recent)
            std = statistics.stdev(recent) if len(recent) > 1 else 0
            forecast_vals = [round(avg, 2)] * horizon
            lower = [round(avg - 1.96 * std, 2)] * horizon
            upper = [round(avg + 1.96 * std, 2)] * horizon

            return NodeResult(
                outputs={
                    "forecast": {"prediction": forecast_vals, "lower": lower, "upper": upper},
                    "metrics": {"method": "moving_average_fallback", "mean": avg, "std": std},
                    "model_used": "moving_average (fallback — install wavqwise for 33 models)",
                },
                message=f"Forecast {horizon} steps (MA fallback, install wavqwise for full models)",
            )
