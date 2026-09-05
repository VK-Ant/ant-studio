"""Ollama local LLM — auto-detect models."""

def ask(prompt: str, system: str = "", model: str = "", host: str = "http://localhost:11434", temperature: float = 0.1) -> str:
    import httpx
    if not model:
        try:
            r = httpx.get(f"{host}/api/tags", timeout=5)
            models = r.json().get("models", [])
            model = models[0]["name"] if models else ""
        except Exception:
            return "[Error: Ollama not running. Start with: ollama serve]"
    if not model:
        return "[Error: No models. Run: ollama pull llama3.2]"
    try:
        resp = httpx.post(f"{host}/api/generate",
            json={"model": model, "prompt": prompt, "system": system,
                  "stream": False, "options": {"temperature": temperature}}, timeout=120)
        if resp.status_code == 404:
            r = httpx.get(f"{host}/api/tags", timeout=5)
            avail = r.json().get("models", [])
            if avail:
                model = avail[0]["name"]
                resp = httpx.post(f"{host}/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False}, timeout=120)
        return resp.json().get("response", "")
    except Exception as e:
        return f"[Ollama error: {e}]"

def list_models(host: str = "http://localhost:11434") -> list:
    try:
        import httpx
        r = httpx.get(f"{host}/api/tags", timeout=5)
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []
