/* Ant Studio — API Client */
import type { NodeManifest, WorkflowJSON, ExecutionResult } from "../types";

const BASE = "/api";

export async function fetchNodes(): Promise<NodeManifest[]> {
  const res = await fetch(`${BASE}/nodes`);
  const data = await res.json();
  return data.nodes;
}

export async function fetchTemplates(): Promise<{ name: string; file: string; description: string }[]> {
  const res = await fetch(`${BASE}/templates`);
  const data = await res.json();
  return data.templates;
}

export async function loadTemplate(name: string): Promise<WorkflowJSON> {
  const res = await fetch(`${BASE}/templates/${name}`);
  return res.json();
}

export async function runWorkflow(workflow: WorkflowJSON): Promise<ExecutionResult> {
  const res = await fetch(`${BASE}/workflows/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(workflow),
  });
  return res.json();
}

export async function saveWorkflow(workflow: WorkflowJSON): Promise<{ saved: string }> {
  const res = await fetch(`${BASE}/workflows/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(workflow),
  });
  return res.json();
}

export async function fetchResources(): Promise<any> {
  const res = await fetch(`${BASE}/resources`);
  return res.json();
}
