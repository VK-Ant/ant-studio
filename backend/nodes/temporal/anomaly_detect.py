"""Anomaly Detection Node — detect anomalies in time-series."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class AnomalyDetectNode(BaseNode):
    node_type = "anomaly_detect"
    label = "Anomaly Detect"
    category = "temporal"
    description = "Detect anomalies in time-series data using WavQWise"
    color = "#ef4444"

    def define_inputs(self):
        return [Port("data", PortType.DICT, "Time-series data")]

    def define_outputs(self):
        return [
            Port("anomalies", PortType.LIST, "Detected anomalies with timestamps and severity"),
            Port("anomaly_count", PortType.FLOAT, "Number of anomalies found"),
            Port("clean_data", PortType.DICT, "Data with anomaly flags added"),
        ]

    def define_config(self):
        return [
            NodeConfig("method", "Detection Method", "select", default="zscore",
                       options=["zscore", "iqr", "isolation_forest", "stl", "dbscan"]),
            NodeConfig("target", "Target Column", "string", default="value"),
            NodeConfig("threshold", "Threshold", "number", default=2.0),
        ]

    async def execute(self, inputs, config, context):
        data = inputs.get("data")
        if not data:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message="No data provided")

        target = config.get("target", "value")
        threshold = float(config.get("threshold", 2.0))
        method = config.get("method", "zscore")

        try:
            from wavqwise import AnomalyPipeline
            import pandas as pd
            df = pd.DataFrame(data)
            detector = AnomalyPipeline()
            detector.load(df, target=target)
            result = detector.detect(method=method)
            anomalies = result.anomalies.to_dict(orient="records") if hasattr(result, 'anomalies') else []
            return NodeResult(
                outputs={"anomalies": anomalies, "anomaly_count": len(anomalies), "clean_data": data},
                message=f"Found {len(anomalies)} anomalies ({method})",
            )
        except ImportError:
            # Z-score fallback
            import statistics
            values = [v for v in data.get(target, []) if isinstance(v, (int, float))]
            if len(values) < 3:
                return NodeResult(outputs={"anomalies": [], "anomaly_count": 0, "clean_data": data})

            mean = statistics.mean(values)
            std = statistics.stdev(values)
            anomalies = []
            for i, v in enumerate(values):
                z = abs(v - mean) / std if std > 0 else 0
                if z > threshold:
                    anomalies.append({"index": i, "value": v, "z_score": round(z, 2),
                                      "severity": "critical" if z > threshold * 2 else "high" if z > threshold * 1.5 else "medium"})

            return NodeResult(
                outputs={"anomalies": anomalies, "anomaly_count": len(anomalies), "clean_data": data},
                message=f"Found {len(anomalies)} anomalies (zscore fallback, install wavqwise for 5 methods)",
            )
