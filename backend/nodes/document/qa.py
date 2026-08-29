"""Document Q&A Node — ask questions about document content."""
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult, NodeStatus

class DocumentQANode(BaseNode):
    node_type = "document_qa"
    label = "Document Q&A"
    category = "document"
    description = "Ask questions about document content using local LLM"
    color = "#8b5cf6"

    def define_inputs(self):
        return [
            Port("text", PortType.TEXT, "Document text (context)"),
            Port("question", PortType.TEXT, "Question to ask", required=False),
        ]

    def define_outputs(self):
        return [
            Port("answer", PortType.TEXT, "Generated answer"),
            Port("confidence", PortType.FLOAT, "Answer confidence"),
            Port("sources", PortType.LIST, "Source references from context"),
        ]

    def define_config(self):
        return [
            NodeConfig("question", "Question", "text_area", default="Summarize this document."),
            NodeConfig("model", "LLM Model", "string", default="llama3.2"),
            NodeConfig("host", "Ollama Host", "string", default="http://localhost:11434"),
            NodeConfig("max_context", "Max Context Chars", "number", default=4000),
            NodeConfig("temperature", "Temperature", "number", default=0.1, min_val=0, max_val=2),
        ]

    async def execute(self, inputs, config, context):
        text = inputs.get("text", "")
        question = inputs.get("question") or config.get("question", "Summarize this document.")
        model = config.get("model", "llama3.2")
        host = config.get("host", "http://localhost:11434")
        max_ctx = int(config.get("max_context", 4000))
        temp = float(config.get("temperature", 0.1))

        if not text:
            return NodeResult(outputs={}, status=NodeStatus.ERROR, message="No document text provided")

        # Truncate context if too long
        truncated = text[:max_ctx] if len(text) > max_ctx else text

        prompt = f"""Based on the following document, answer the question accurately.
If the answer is not in the document, say "Not found in document."
Always cite which part of the document your answer comes from.

DOCUMENT:
{truncated}

QUESTION: {question}

ANSWER:"""

        try:
            import httpx
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{host}/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False,
                          "options": {"temperature": temp}},
                )
                resp.raise_for_status()
                result = resp.json()
                answer = result.get("response", "").strip()

                # Basic confidence: check if answer references document content
                doc_words = set(text.lower().split())
                answer_words = set(answer.lower().split())
                overlap = len(doc_words & answer_words) / len(answer_words) if answer_words else 0
                confidence = min(overlap * 2, 1.0)  # Scale up, cap at 1.0

                # Find source sentences
                sources = []
                for sentence in text.split("."):
                    s = sentence.strip()
                    if s and any(w in s.lower() for w in answer.lower().split()[:5]):
                        sources.append(s[:200])
                    if len(sources) >= 3:
                        break

                return NodeResult(
                    outputs={"answer": answer, "confidence": round(confidence, 3), "sources": sources},
                    message=f"Answered using {model} ({len(answer)} chars)",
                )
        except ImportError:
            return NodeResult(outputs={}, status=NodeStatus.ERROR,
                              message="pip install httpx required for Ollama")
        except Exception as e:
            # Fallback: keyword extraction answer
            sentences = [s.strip() for s in text.split(".") if s.strip()]
            q_words = set(question.lower().split())
            scored = [(s, len(set(s.lower().split()) & q_words)) for s in sentences]
            scored.sort(key=lambda x: x[1], reverse=True)
            best = scored[:3] if scored else []
            answer = ". ".join([s for s, _ in best if _ > 0]) or "Could not find relevant answer."

            return NodeResult(
                outputs={"answer": answer, "confidence": 0.3, "sources": [s for s, _ in best[:2]]},
                message=f"Keyword match fallback (Ollama unavailable: {e})",
            )
