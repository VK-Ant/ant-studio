/* Ant Studio — WebSocket Hook for Live Execution */
import { useCallback, useRef } from "react";
import { useWorkflowStore } from "../store/workflowStore";

export function useExecution() {
  const wsRef = useRef<WebSocket | null>(null);
  const { toWorkflowJSON, updateNodeStatus, setExecuting, resetStatuses, setLastResult } = useWorkflowStore();

  const execute = useCallback(() => {
    const workflow = toWorkflowJSON();
    resetStatuses();
    setExecuting(true);
    setLastResult(null);

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/execute`);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify(workflow));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "node_status") {
        updateNodeStatus(msg.node_id, msg.status, msg.message, msg.time_ms);
      } else if (msg.type === "workflow_complete") {
        setLastResult(msg);
        setExecuting(false);
      } else if (msg.type === "error") {
        console.error("Execution error:", msg.message);
        setExecuting(false);
      }
    };

    ws.onerror = () => {
      // Fallback to REST if WebSocket fails
      console.warn("WebSocket failed, falling back to REST");
      fetch("/api/workflows/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(workflow),
      })
        .then((r) => r.json())
        .then((result) => {
          Object.entries(result.results).forEach(([nodeId, r]: [string, any]) => {
            updateNodeStatus(nodeId, r.status, r.message, r.time_ms, r.outputs);
          });
          setLastResult(result);
          setExecuting(false);
        })
        .catch((e) => {
          console.error("REST fallback failed:", e);
          setExecuting(false);
        });
    };

    ws.onclose = () => {
      setExecuting(false);
    };
  }, [toWorkflowJSON, updateNodeStatus, setExecuting, resetStatuses, setLastResult]);

  const cancel = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    setExecuting(false);
  }, [setExecuting]);

  return { execute, cancel };
}
