"""
Ant Studio — Base Node Contract
Every node in Ant Studio inherits from BaseNode.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class PortType(str, Enum):
    FILE = "file"
    IMAGE = "image"
    TEXT = "text"
    DICT = "dict"
    LIST = "list"
    FLOAT = "float"
    BOOL = "bool"
    ANY = "any"


@dataclass
class Port:
    name: str
    port_type: PortType
    description: str = ""
    required: bool = True


@dataclass
class NodeConfig:
    key: str
    label: str
    config_type: str  # "string", "number", "select", "boolean", "text_area", "file"
    default: Any = None
    options: List[str] = field(default_factory=list)
    min_val: Optional[float] = None
    max_val: Optional[float] = None


class NodeStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class NodeResult:
    outputs: Dict[str, Any]
    status: NodeStatus = NodeStatus.SUCCESS
    message: str = ""
    execution_time_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    workflow_id: str = ""
    execution_id: str = ""
    data_dir: str = "./data"
    on_status: Optional[Any] = None  # async callback


class BaseNode(ABC):
    """Base class for all Ant Studio nodes."""

    node_type: str = ""
    label: str = ""
    category: str = ""
    description: str = ""
    version: str = "0.1.0"
    color: str = "#6366f1"  # default indigo

    def __init__(self):
        self.inputs: List[Port] = self.define_inputs()
        self.outputs: List[Port] = self.define_outputs()
        self.config: List[NodeConfig] = self.define_config()

    @abstractmethod
    def define_inputs(self) -> List[Port]:
        """Return list of input ports."""

    @abstractmethod
    def define_outputs(self) -> List[Port]:
        """Return list of output ports."""

    def define_config(self) -> List[NodeConfig]:
        """Return configurable parameters. Override if needed."""
        return []

    @abstractmethod
    async def execute(
        self,
        inputs: Dict[str, Any],
        config: Dict[str, Any],
        context: ExecutionContext,
    ) -> NodeResult:
        """Run the node logic."""

    def to_manifest(self) -> dict:
        """Serialize node definition for frontend."""
        return {
            "node_type": self.node_type,
            "label": self.label,
            "category": self.category,
            "description": self.description,
            "version": self.version,
            "color": self.color,
            "inputs": [
                {
                    "name": p.name,
                    "type": p.port_type.value,
                    "description": p.description,
                    "required": p.required,
                }
                for p in self.inputs
            ],
            "outputs": [
                {
                    "name": p.name,
                    "type": p.port_type.value,
                    "description": p.description,
                }
                for p in self.outputs
            ],
            "config": [
                {
                    "key": c.key,
                    "label": c.label,
                    "type": c.config_type,
                    "default": c.default,
                    "options": c.options,
                    "min": c.min_val,
                    "max": c.max_val,
                }
                for c in self.config
            ],
        }
