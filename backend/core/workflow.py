"""
Ant Studio — Workflow Model
Defines the JSON workflow format and parsing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import uuid


@dataclass
class WorkflowNode:
    instance_id: str
    node_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})


@dataclass
class Connection:
    source: str       # source node instance_id
    source_port: str  # output port name
    target: str       # target node instance_id
    target_port: str  # input port name


@dataclass
class Workflow:
    id: str = ""
    name: str = "Untitled"
    description: str = ""
    version: str = "1.0"
    nodes: List[WorkflowNode] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        nodes = [
            WorkflowNode(
                instance_id=n.get("instance_id", str(uuid.uuid4())[:8]),
                node_type=n["node_type"],
                config=n.get("config", {}),
                position=n.get("position", {"x": 0, "y": 0}),
            )
            for n in data.get("nodes", [])
        ]
        connections = [
            Connection(
                source=c["source"],
                source_port=c["source_port"],
                target=c["target"],
                target_port=c["target_port"],
            )
            for c in data.get("connections", [])
        ]
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            nodes=nodes,
            connections=connections,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "nodes": [
                {
                    "instance_id": n.instance_id,
                    "node_type": n.node_type,
                    "config": n.config,
                    "position": n.position,
                }
                for n in self.nodes
            ],
            "connections": [
                {
                    "source": c.source,
                    "source_port": c.source_port,
                    "target": c.target,
                    "target_port": c.target_port,
                }
                for c in self.connections
            ],
        }

    @classmethod
    def from_json(cls, path: str) -> "Workflow":
        with open(path, "r") as f:
            return cls.from_dict(json.load(f))

    def to_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
