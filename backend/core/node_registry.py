"""
Ant Studio — Node Registry
Central lookup: node_type string -> BaseNode class
"""

from typing import Dict, Type, List
from .base_node import BaseNode


class NodeRegistry:
    def __init__(self):
        self._nodes: Dict[str, Type[BaseNode]] = {}

    def register(self, node_class: Type[BaseNode]):
        """Register a node class. Can be used as decorator."""
        instance = node_class()
        self._nodes[instance.node_type] = node_class
        return node_class

    def get(self, node_type: str) -> BaseNode:
        """Get a new instance of a registered node."""
        if node_type not in self._nodes:
            raise KeyError(f"Unknown node type: '{node_type}'. Available: {list(self._nodes.keys())}")
        return self._nodes[node_type]()

    def list_manifests(self) -> List[dict]:
        """Return all node manifests for frontend."""
        return [cls().to_manifest() for cls in self._nodes.values()]

    def list_categories(self) -> Dict[str, List[dict]]:
        """Return manifests grouped by category."""
        result: Dict[str, List[dict]] = {}
        for manifest in self.list_manifests():
            cat = manifest["category"]
            result.setdefault(cat, []).append(manifest)
        return result

    @property
    def count(self) -> int:
        return len(self._nodes)


# Global registry instance
registry = NodeRegistry()
