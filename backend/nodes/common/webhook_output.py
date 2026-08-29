"""Webhook/API Output Node — send results to HTTP endpoint."""
import json
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class WebhookOutputNode(BaseNode):
    node_type = "webhook_output"
    label = "Webhook / API Output"
    category = "output"
    description = "Send results to an HTTP webhook or REST API endpoint"
    color = "#059669"

    def define_inputs(self):
        return [Port("data", PortType.ANY, "Data to send")]

    def define_outputs(self):
        return [
            Port("response", PortType.TEXT, "API response"),
            Port("status_code", PortType.FLOAT, "HTTP status code"),
        ]

    def define_config(self):
        return [
            NodeConfig("url", "Webhook URL", "string", default="https://example.com/webhook"),
            NodeConfig("method", "HTTP Method", "select", default="POST", options=["POST", "PUT", "PATCH"]),
            NodeConfig("headers", "Headers (JSON)", "text_area", default='{"Content-Type": "application/json"}'),
            NodeConfig("auth_token", "Auth Token (Bearer)", "string", default=""),
        ]

    async def execute(self, inputs, config, context):
        data = inputs.get("data")
        url = config.get("url", "")
        method = config.get("method", "POST")

        try:
            headers = json.loads(config.get("headers", "{}"))
        except json.JSONDecodeError:
            headers = {"Content-Type": "application/json"}

        auth_token = config.get("auth_token", "")
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.request(method, url, json=data, headers=headers)
                return NodeResult(
                    outputs={"response": resp.text[:1000], "status_code": resp.status_code},
                    message=f"{method} {url} → {resp.status_code}",
                )
        except Exception as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Webhook failed: {e}")
