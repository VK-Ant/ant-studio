"""AntGuard Start Node — begin privacy monitoring."""
import time
from backend.core.base_node import BaseNode, Port, PortType, NodeConfig, NodeResult

class GuardStartNode(BaseNode):
    node_type = "guard_start"
    label = "AntGuard Start"
    category = "backbone"
    description = "Start monitoring file/network activity for privacy audit"
    color = "#10b981"

    def define_inputs(self):
        return []

    def define_outputs(self):
        return [Port("guard_session", PortType.DICT, "Guard session info")]

    def define_config(self):
        return [
            NodeConfig("watch_dirs", "Watch Directories", "string", default="./data,./output"),
            NodeConfig("monitor_network", "Monitor Network", "boolean", default=True),
        ]

    async def execute(self, inputs, config, context):
        session = {
            "session_id": context.execution_id,
            "start_time": time.time(),
            "watch_dirs": config.get("watch_dirs", "").split(","),
            "monitor_network": config.get("monitor_network", True),
            "events": [],
        }

        try:
            from antguard import Guard
            guard = Guard(watch=session["watch_dirs"])
            guard.start()
            session["guard_instance"] = id(guard)
            session["antguard_available"] = True
        except ImportError:
            session["antguard_available"] = False

        return NodeResult(outputs={"guard_session": session}, message="AntGuard monitoring started")
