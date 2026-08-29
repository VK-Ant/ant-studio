"""
Ant Studio — Resource Manager
Tracks loaded models, GPU memory, LRU eviction.
"""

import time
import logging
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger("antstudio.resources")


@dataclass
class LoadedModel:
    name: str
    model: Any
    memory_mb: float
    last_used: float


class ResourceManager:
    def __init__(self, max_memory_mb: float = 6000):
        self._models: Dict[str, LoadedModel] = {}
        self.max_memory_mb = max_memory_mb

    def get_model(self, name: str, loader_fn: Callable) -> Any:
        """Get model from cache or load it. loader_fn returns (model, memory_mb)."""
        if name in self._models:
            self._models[name].last_used = time.time()
            logger.debug(f"Model cache hit: {name}")
            return self._models[name].model

        self._evict_if_needed()

        logger.info(f"Loading model: {name}")
        model, mem_mb = loader_fn()

        self._models[name] = LoadedModel(
            name=name,
            model=model,
            memory_mb=mem_mb,
            last_used=time.time(),
        )
        logger.info(f"Model loaded: {name} ({mem_mb:.0f}MB)")
        return model

    def _evict_if_needed(self):
        """Remove least-recently-used models if memory is above 80%."""
        used = sum(m.memory_mb for m in self._models.values())
        while used > self.max_memory_mb * 0.8 and self._models:
            oldest = min(self._models.values(), key=lambda m: m.last_used)
            logger.info(f"Evicting model: {oldest.name} ({oldest.memory_mb:.0f}MB)")
            del self._models[oldest.name]
            used -= oldest.memory_mb

    def unload(self, name: str):
        """Manually unload a model."""
        if name in self._models:
            del self._models[name]
            logger.info(f"Unloaded model: {name}")

    def status(self) -> dict:
        """Current resource status."""
        gpu_info = self._get_gpu_info()
        return {
            "models_loaded": list(self._models.keys()),
            "model_memory_mb": sum(m.memory_mb for m in self._models.values()),
            "max_memory_mb": self.max_memory_mb,
            "gpu": gpu_info,
        }

    def _get_gpu_info(self) -> dict:
        """Try to get GPU info via torch or pynvml."""
        try:
            import torch
            if torch.cuda.is_available():
                return {
                    "available": True,
                    "name": torch.cuda.get_device_name(0),
                    "memory_total_mb": torch.cuda.get_device_properties(0).total_mem / 1e6,
                    "memory_used_mb": torch.cuda.memory_allocated(0) / 1e6,
                }
        except ImportError:
            pass
        return {"available": False}


# Global instance
resources = ResourceManager()
