"""Document Q&A — ask questions with RAG modes."""
from typing import Optional
from antstudio.backbone import Backbone
from antstudio.io.reader import read_input
from antstudio.doc.loader import load_text
from antstudio.llm.engine import LLMEngine

class Answer:
    def __init__(self, text: str, confidence: float, sources: list, quality: dict, audit: dict):
        self.text = text
        self.confidence = confidence
        self.sources = sources
        self.quality = quality
        self.audit = audit
    def __repr__(self):
        return f"Answer(confidence={self.confidence}, len={len(self.text)})"

def run(source: str, question: str, rag: str = "auto", model: str = "",
        system_prompt: str = "", verbose: bool = True, **kwargs) -> Answer:

    bb = Backbone(f"doc ask {source}")
    bb.start()

    if verbose:
        print(f"\n  Ant Studio v0.1.0 | DocQWise + Ollama + llmevalkit + AntGuard\n")

    items = read_input(source=source, extensions=".pdf,.docx,.txt")
    if not items:
        audit = bb.finish()
        return Answer("No documents found.", 0, [], {}, audit)

    # Load all texts
    texts = []
    for fname, raw, fpath in items:
        t = load_text(raw, fname)
        if t and not t.startswith("["):
            texts.append({"text": t, "source": fname})

    if verbose:
        print(f"  [1/4] Loading {'.' * 21} {len(texts)} documents")

    # Route RAG mode
    if rag == "auto":
        rag = "graph" if len(texts) > 1 else "simple"
        route = bb.route(source)
        if verbose:
            print(f"  [2/4] Routing {'.' * 21} {rag} RAG (adaptive: {route})")

    # Build context
    if rag == "graph":
        context = _graph_rag(texts, question)
    else:
        context = _simple_rag(texts, question)

    # Generate answer
    sys = system_prompt or "You are a precise document analyst. Answer only from the provided evidence."
    prompt = f"Evidence:\n{context[:4000]}\n\nQuestion: {question}\n\nAnswer:"
    engine = LLMEngine(model=model)
    answer_text = engine.ask(prompt, system=sys)

    if verbose:
        print(f"  [3/4] Reasoning {'.' * 19} {len(answer_text)} chars")

    # Quality check
    q = bb.evaluate("answer", answer_text, context[:1000])
    audit = bb.finish()

    # Find sources
    sources = []
    for t in texts:
        for sent in t["text"].split(".")[:20]:
            if any(w in sent.lower() for w in question.lower().split()[:3]):
                sources.append(f"{t['source']}: {sent.strip()[:80]}")
                if len(sources) >= 3:
                    break

    confidence = q.get("score", 0.5)

    if verbose:
        dl = audit["privacy"]["data_left_system"]
        print(f"  [4/4] Audit {'.' * 23} data_left: {'YES' if dl else 'NO'}")
        print(f"\n  Answer: {answer_text[:200]}{'...' if len(answer_text) > 200 else ''}")
        print(f"  Confidence: {confidence:.0%}")
        print(f"\n  Done in {audit['duration_seconds']}s\n")

    return Answer(answer_text, confidence, sources, bb.quality_scores, audit)


def _simple_rag(texts: list, question: str) -> str:
    all_text = "\n\n---\n\n".join(t["text"][:2000] for t in texts[:5])
    return all_text

def _graph_rag(texts: list, question: str) -> str:
    """Graph-based retrieval — find connected evidence."""
    try:
        from antstudio.doc.extract import _extract_regex
        entities = set()
        for t in texts:
            fields = _extract_regex(t["text"], ["vendor", "invoice_number", "amount"])
            for v in fields.get("fields", {}).values():
                if v:
                    entities.add(v.lower())

        # Find sentences mentioning shared entities
        relevant = []
        q_words = set(question.lower().split())
        for t in texts:
            for sent in t["text"].split("."):
                sent_lower = sent.lower()
                if any(e in sent_lower for e in entities) or any(w in sent_lower for w in q_words):
                    relevant.append(f"[{t['source']}] {sent.strip()}")

        return "\n".join(relevant[:30]) if relevant else _simple_rag(texts, question)
    except Exception:
        return _simple_rag(texts, question)
