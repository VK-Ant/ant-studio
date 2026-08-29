/* Ant Studio — Canvas (React Flow Wrapper) */
import { useCallback } from "react";
import { ReactFlow, Background, Controls, MiniMap, ReactFlowProvider } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useWorkflowStore } from "../store/workflowStore";
import AntNode from "../nodes/AntNode";
import type { NodeManifest } from "../types";

const nodeTypes = { antNode: AntNode };

function CanvasInner() {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, addNode, selectNode, manifests } = useWorkflowStore();

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const data = event.dataTransfer.getData("application/antstudio-node");
      if (!data) return;

      const manifest: NodeManifest = JSON.parse(data);
      const bounds = (event.target as HTMLElement).closest(".react-flow")?.getBoundingClientRect();
      if (!bounds) return;

      const position = {
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top,
      };
      addNode(manifest, position);
    },
    [addNode]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onNodeClick = useCallback((_: any, node: any) => {
    selectNode(node.id);
  }, [selectNode]);

  const onPaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  return (
    <div className="flex-1" onDrop={onDrop} onDragOver={onDragOver}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        snapToGrid
        snapGrid={[15, 15]}
        defaultEdgeOptions={{ animated: true, style: { stroke: "#6366f1", strokeWidth: 2 } }}
        style={{ backgroundColor: "#0f1117" }}
      >
        <Background color="#1e293b" gap={20} size={1} />
        <Controls position="bottom-left" style={{ background: "#1e293b", border: "1px solid #334155" }} />
        <MiniMap
          position="bottom-right"
          style={{ background: "#1e293b", border: "1px solid #334155" }}
          nodeColor={(n) => (n.data as any)?.color || "#6366f1"}
          maskColor="rgba(0,0,0,0.6)"
        />
      </ReactFlow>
    </div>
  );
}

export default function Canvas() {
  return (
    <ReactFlowProvider>
      <CanvasInner />
    </ReactFlowProvider>
  );
}
