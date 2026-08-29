"""Ollama LLM Node — local LLM inference."""
import json
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class OllamaLLMNode(BaseNode):
    node_type = "ollama_llm"
    label = "Ollama LLM"
    category = "backbone"
    description = "Run local LLM inference via Ollama"
    color = "#f97316"

    def define_inputs(self):
        return [
            Port("prompt", PortType.TEXT, "Prompt text"),
            Port("context", PortType.TEXT, "Context to include", required=False),
        ]

    def define_outputs(self):
        return [Port("response", PortType.TEXT, "LLM response")]

    def define_config(self):
        return [
            NodeConfig("model", "Model", "string", default="llama3.2"),
            NodeConfig("host", "Ollama Host", "string", default="http://localhost:11434"),
            NodeConfig("temperature", "Temperature", "number", default=0.1, min_val=0, max_val=2),
            NodeConfig("system_prompt", "System Prompt", "text_area", default="You are a helpful AI assistant."),
        ]

    async def execute(self, inputs, config, context):
        prompt = inputs.get("prompt", "")
        ctx = inputs.get("context", "")
        if ctx:
            prompt = f"Context:\n{ctx}\n\nQuestion:\n{prompt}"

        model = config.get("model", "llama3.2")
        host = config.get("host", "http://localhost:11434")
        temp = config.get("temperature", 0.1)
        system = config.get("system_prompt", "You are a helpful AI assistant.")

        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{host}/api/generate",
                    json={"model": model, "prompt": prompt, "system": system, "stream": False,
                          "options": {"temperature": temp}},
                )
                resp.raise_for_status()
                result = resp.json()
                return NodeResult(
                    outputs={"response": result.get("response", "")},
                    message=f"Generated {len(result.get('response', ''))} chars via {model}",
                )
        except ImportError:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message="pip install httpx required")
        except Exception as e:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message=f"Ollama error: {e}")
