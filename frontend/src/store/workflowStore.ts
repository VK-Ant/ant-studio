/* Ant Studio — Global State (Zustand) */
import { create } from "zustand";
import { Node, Edge, OnNodesChange, OnEdgesChange, applyNodeChanges, applyEdgeChanges, Connection, addEdge } from "@xyflow/react";
import type { WorkflowNodeData, NodeManifest, ExecutionResult, WorkflowJSON } from "../types";

interface WorkflowStore {
  // Canvas state
  nodes: Node<WorkflowNodeData>[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: (connection: Connection) => void;

  // Node catalog
  manifests: NodeManifest[];
  setManifests: (m: NodeManifest[]) => void;

  // Selection
  selectedNodeId: string | null;
  selectNode: (id: string | null) => void;

  // Execution
  isExecuting: boolean;
  setExecuting: (v: boolean) => void;
  updateNodeStatus: (nodeId: string, status: string, message?: string, timeMs?: number, outputs?: Record<string, any>) => void;
  resetStatuses: () => void;

  // Workflow operations
  addNode: (manifest: NodeManifest, position: { x: number; y: number }) => void;
  removeNode: (id: string) => void;
  updateNodeConfig: (id: string, key: string, value: any) => void;
  loadWorkflow: (wf: WorkflowJSON, manifests: NodeManifest[]) => void;
  toWorkflowJSON: () => WorkflowJSON;
  clearCanvas: () => void;

  // Results
  lastResult: ExecutionResult | null;
  setLastResult: (r: ExecutionResult | null) => void;
}

let nodeCounter = 0;

export const useWorkflowStore = create<WorkflowStore>((set, get) => ({
  nodes: [],
  edges: [],
  manifests: [],
  selectedNodeId: null,
  isExecuting: false,
  lastResult: null,

  onNodesChange: (changes) => set({ nodes: applyNodeChanges(changes, get().nodes) as Node<WorkflowNodeData>[] }),
  onEdgesChange: (changes) => set({ edges: applyEdgeChanges(changes, get().edges) }),
  onConnect: (connection) => set({ edges: addEdge({ ...connection, animated: true, style: { stroke: "#6366f1" } }, get().edges) }),

  setManifests: (m) => set({ manifests: m }),
  selectNode: (id) => set({ selectedNodeId: id }),
  setExecuting: (v) => set({ isExecuting: v }),
  setLastResult: (r) => set({ lastResult: r }),

  addNode: (manifest, position) => {
    const id = `${manifest.node_type}_${++nodeCounter}`;
    const defaultConfig: Record<string, any> = {};
    manifest.config.forEach((c) => { defaultConfig[c.key] = c.default; });

    const newNode: Node<WorkflowNodeData> = {
      id,
      type: "antNode",
      position,
      data: {
        node_type: manifest.node_type,
        label: manifest.label,
        category: manifest.category,
        color: manifest.color,
        config: defaultConfig,
        manifest,
        status: "idle",
      },
    };
    set({ nodes: [...get().nodes, newNode] });
  },

  removeNode: (id) => {
    set({
      nodes: get().nodes.filter((n) => n.id !== id),
      edges: get().edges.filter((e) => e.source !== id && e.target !== id),
      selectedNodeId: get().selectedNodeId === id ? null : get().selectedNodeId,
    });
  },

  updateNodeConfig: (id, key, value) => {
    set({
      nodes: get().nodes.map((n) =>
        n.id === id ? { ...n, data: { ...n.data, config: { ...n.data.config, [key]: value } } } : n
      ),
    });
  },

  updateNodeStatus: (nodeId, status, message, timeMs, outputs) => {
    set({
      nodes: get().nodes.map((n) =>
        n.id === nodeId
          ? { ...n, data: { ...n.data, status: status as any, message, timeMs, outputs } }
          : n
      ),
    });
  },

  resetStatuses: () => {
    set({
      nodes: get().nodes.map((n) => ({
        ...n,
        data: { ...n.data, status: "idle", message: undefined, timeMs: undefined, outputs: undefined },
      })),
    });
  },

  loadWorkflow: (wf, manifests) => {
    const manifestMap = Object.fromEntries(manifests.map((m) => [m.node_type, m]));
    const nodes: Node<WorkflowNodeData>[] = wf.nodes.map((n) => {
      const manifest = manifestMap[n.node_type];
      return {
        id: n.instance_id,
        type: "antNode",
        position: n.position,
        data: {
          node_type: n.node_type,
          label: manifest?.label || n.node_type,
          category: manifest?.category || "unknown",
          color: manifest?.color || "#6366f1",
          config: n.config,
          manifest: manifest || ({} as NodeManifest),
          status: "idle",
        },
      };
    });
    const edges: Edge[] = wf.connections.map((c, i) => ({
      id: `e${i}`,
      source: c.source,
      sourceHandle: c.source_port,
      target: c.target,
      targetHandle: c.target_port,
      animated: true,
      style: { stroke: "#6366f1" },
    }));
    set({ nodes, edges, selectedNodeId: null, lastResult: null });
  },

  toWorkflowJSON: () => {
    const { nodes, edges } = get();
    return {
      id: `wf_${Date.now()}`,
      name: "Untitled Workflow",
      description: "",
      version: "1.0",
      nodes: nodes.map((n) => ({
        instance_id: n.id,
        node_type: n.data.node_type,
        config: n.data.config,
        position: n.position,
      })),
      connections: edges.map((e) => ({
        source: e.source,
        source_port: e.sourceHandle || "output",
        target: e.target,
        target_port: e.targetHandle || "input",
      })),
    };
  },

  clearCanvas: () => set({ nodes: [], edges: [], selectedNodeId: null, lastResult: null }),
}));
