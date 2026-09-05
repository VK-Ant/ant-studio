"""Universal LLM engine — Ollama, LiteLLM, OpenAI, Azure, HuggingFace, local models.

Supports every provider through a single interface:

    from antstudio.llm.engine import LLMEngine

    # Auto-detect (tries Ollama first, then LiteLLM)
    engine = LLMEngine()

    # Specific providers
    engine = LLMEngine(provider="ollama", model="llama3.2")
    engine = LLMEngine(provider="openai", model="gpt-4o")
    engine = LLMEngine(provider="azure", model="gpt-4o", api_base="https://xxx.openai.azure.com/", api_key="...")
    engine = LLMEngine(provider="huggingface", model="mistralai/Mistral-7B-v0.1")
    engine = LLMEngine(provider="anthropic", model="claude-sonnet-4-20250514")
    engine = LLMEngine(provider="local", model_path="/path/to/model.gguf")

Model string format (LiteLLM style):
    ollama/llama3.2
    openai/gpt-4o
    azure/gpt-4o
    huggingface/mistralai/Mistral-7B-v0.1
    anthropic/claude-sonnet-4-20250514
"""
import os
from typing import Optional


class LLMEngine:
    """Universal LLM interface — one class, every provider."""

    def __init__(self, provider: str = "auto", model: str = "",
                 api_key: str = "", api_base: str = "",
                 model_path: str = "", temperature: float = 0.1,
                 max_tokens: int = 2048):
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.api_base = api_base
        self.model_path = model_path
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Parse model string: "openai/gpt-4o" -> provider=openai, model=gpt-4o
        if "/" in model and provider == "auto":
            parts = model.split("/", 1)
            if parts[0] in ("ollama", "openai", "azure", "huggingface",
                            "anthropic", "groq", "mistral", "together_ai",
                            "deepseek", "local"):
                self.provider = parts[0]
                self.model = parts[1]

        # Resolve provider from env
        if self.provider == "auto":
            self.provider = self._detect_provider()

    def ask(self, prompt: str, system: str = "") -> str:
        """Send a prompt and get a response. Works with any provider."""
        if self.provider == "ollama":
            return self._ask_ollama(prompt, system)
        elif self.provider == "local":
            return self._ask_local(prompt, system)
        else:
            return self._ask_litellm(prompt, system)

    def list_models(self) -> list:
        """List available models for the current provider."""
        if self.provider == "ollama":
            return _ollama_models(self.api_base or "http://localhost:11434")
        elif self.provider in ("openai", "azure", "anthropic", "huggingface",
                               "groq", "mistral", "together_ai", "deepseek"):
            return [self.model] if self.model else [f"Configure {self.provider} model"]
        elif self.provider == "local":
            return [self.model_path] if self.model_path else ["No local model configured"]
        return []

    def info(self) -> dict:
        """Current engine configuration."""
        return {
            "provider": self.provider,
            "model": self.model or self.model_path or "auto",
            "api_base": self.api_base or "default",
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    # --- Provider implementations ---

    def _detect_provider(self) -> str:
        """Auto-detect best available provider."""
        # 1. Ollama running locally?
        if _ollama_models():
            return "ollama"
        # 2. LiteLLM with any API key configured?
        for key in ("OPENAI_API_KEY", "AZURE_API_KEY", "ANTHROPIC_API_KEY",
                     "HUGGINGFACE_API_KEY", "GROQ_API_KEY", "MISTRAL_API_KEY",
                     "TOGETHER_API_KEY", "DEEPSEEK_API_KEY", "LLM_API_KEY"):
            if os.environ.get(key):
                return self._provider_from_key(key)
        # 3. Fallback
        return "ollama"

    def _provider_from_key(self, key: str) -> str:
        mapping = {
            "OPENAI_API_KEY": "openai",
            "AZURE_API_KEY": "azure",
            "ANTHROPIC_API_KEY": "anthropic",
            "HUGGINGFACE_API_KEY": "huggingface",
            "GROQ_API_KEY": "groq",
            "MISTRAL_API_KEY": "mistral",
            "TOGETHER_API_KEY": "together_ai",
            "DEEPSEEK_API_KEY": "deepseek",
        }
        return mapping.get(key, "openai")

    def _ask_ollama(self, prompt: str, system: str) -> str:
        """Ollama local models — zero config."""
        host = self.api_base or "http://localhost:11434"
        model = self.model
        try:
            import httpx
        except ImportError:
            return "[Error: pip install httpx]"

        if not model:
            models = _ollama_models(host)
            model = models[0] if models else ""
        if not model:
            return "[Error: No Ollama models. Run: ollama pull llama3.2]"

        try:
            resp = httpx.post(f"{host}/api/generate",
                json={"model": model, "prompt": prompt, "system": system,
                      "stream": False,
                      "options": {"temperature": self.temperature, "num_predict": self.max_tokens}},
                timeout=120)
            if resp.status_code == 404:
                models = _ollama_models(host)
                if models:
                    model = models[0]
                    resp = httpx.post(f"{host}/api/generate",
                        json={"model": model, "prompt": prompt, "system": system,
                              "stream": False}, timeout=120)
            return resp.json().get("response", "")
        except Exception as e:
            return f"[Ollama error: {e}. Start with: ollama serve]"

    def _ask_litellm(self, prompt: str, system: str) -> str:
        """LiteLLM — 100+ providers through one interface."""
        try:
            from litellm import completion
        except ImportError:
            return "[Error: pip install litellm]"

        # Build model string for litellm
        model_str = self.model
        if self.provider != "auto" and "/" not in model_str:
            model_str = f"{self.provider}/{model_str}"

        # Set API keys from env or explicit
        kwargs = {
            "model": model_str,
            "messages": [],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if system:
            kwargs["messages"].append({"role": "system", "content": system})
        kwargs["messages"].append({"role": "user", "content": prompt})

        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        try:
            resp = completion(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e:
            return f"[LLM error ({self.provider}): {e}]"

    def _ask_local(self, prompt: str, system: str) -> str:
        """Local GGUF/GGML models via llama-cpp-python."""
        try:
            from llama_cpp import Llama
        except ImportError:
            return "[Error: pip install llama-cpp-python]"

        if not self.model_path:
            return "[Error: No model_path specified for local model]"

        try:
            llm = Llama(model_path=self.model_path, n_ctx=4096, verbose=False)
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            output = llm(full_prompt, max_tokens=self.max_tokens,
                         temperature=self.temperature)
            return output["choices"][0]["text"].strip()
        except Exception as e:
            return f"[Local model error: {e}]"

    def __repr__(self):
        return f"LLMEngine(provider={self.provider}, model={self.model or 'auto'})"


# --- Module-level helpers (backward compat with ollama.py) ---

def _ollama_models(host: str = "http://localhost:11434") -> list:
    """List Ollama models. Returns empty list if Ollama not running."""
    try:
        import httpx
        r = httpx.get(f"{host}/api/tags", timeout=5)
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


# Backward-compatible functions for existing code
def ask(prompt: str, system: str = "", model: str = "", host: str = "",
        temperature: float = 0.1) -> str:
    """Drop-in replacement for ollama.ask()."""
    engine = LLMEngine(model=model, api_base=host, temperature=temperature)
    return engine.ask(prompt, system)


def list_models(host: str = "http://localhost:11434") -> list:
    """Drop-in replacement for ollama.list_models()."""
    return _ollama_models(host)
