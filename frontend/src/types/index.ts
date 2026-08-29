/* Ant Studio — TypeScript Types */

export interface PortDef {
  name: string;
  type: string;
  description: string;
  required?: boolean;
}

export interface ConfigDef {
  key: string;
  label: string;
  type: string; // "string" | "number" | "select" | "boolean" | "text_area"
  default: any;
  options?: string[];
  min?: number;
  max?: number;
}

export interface NodeManifest {
  node_type: string;
  label: string;
  category: string;
  description: string;
  version: string;
  color: string;
  inputs: PortDef[];
  outputs: PortDef[];
  config: ConfigDef[];
}

export interface WorkflowNodeData {
  node_type: string;
  label: string;
  category: string;
  color: string;
  config: Record<string, any>;
  manifest: NodeManifest;
  status?: "idle" | "running" | "success" | "error" | "skipped";
  message?: string;
  timeMs?: number;
  outputs?: Record<string, any>;
}

export interface WorkflowJSON {
  id: string;
  name: string;
  description: string;
  version: string;
  nodes: { instance_id: string; node_type: string; config: Record<string, any>; position: { x: number; y: number } }[];
  connections: { source: string; source_port: string; target: string; target_port: string }[];
}

export interface ExecutionResult {
  execution_id: string;
  results: Record<string, {
    status: string;
    message: string;
    time_ms: number;
    outputs: Record<string, any>;
  }>;
}
