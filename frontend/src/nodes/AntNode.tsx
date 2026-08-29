/* Ant Studio — Custom Node Component */
import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import type { WorkflowNodeData } from "../types";

const statusColors: Record<string, string> = {
  idle: "border-gray-600",
  running: "border-blue-500 shadow-blue-500/30 shadow-lg",
  success: "border-green-500",
  error: "border-red-500",
  skipped: "border-gray-500 opacity-50",
};

const statusIcons: Record<string, string> = {
  idle: "○",
  running: "◉",
  success: "✓",
  error: "✕",
  skipped: "—",
};

const categoryLabels: Record<string, string> = {
  common: "INPUT",
  document: "DOCQWISE",
  backbone: "BACKBONE",
  output: "OUTPUT",
};

function AntNode({ data, selected }: { data: WorkflowNodeData; selected: boolean }) {
  const status = data.status || "idle";
  const manifest = data.manifest;

  return (
    <div
      className={`rounded-lg border-2 ${statusColors[status]} ${
        selected ? "ring-2 ring-indigo-400" : ""
      } bg-gray-900 min-w-[180px] max-w-[220px] transition-all duration-300`}
    >
      {/* Header */}
      <div
        className="px-3 py-1.5 rounded-t-md text-xs font-bold tracking-wider uppercase"
        style={{ backgroundColor: data.color + "22", color: data.color }}
      >
        {categoryLabels[data.category] || data.category.toUpperCase()}
      </div>

      {/* Title + Status */}
      <div className="px-3 py-2 flex items-center gap-2">
        <span
          className={`text-sm font-semibold ${
            status === "running" ? "text-blue-400 animate-pulse" : "text-white"
          }`}
        >
          {data.label}
        </span>
        <span className={`text-xs ml-auto ${status === "error" ? "text-red-400" : status === "success" ? "text-green-400" : "text-gray-500"}`}>
          {statusIcons[status]}
        </span>
      </div>

      {/* Message / Time */}
      {(data.message || data.timeMs) && (
        <div className="px-3 pb-2 text-[10px] text-gray-400 truncate">
          {data.timeMs ? `${data.timeMs.toFixed(0)}ms` : ""} {data.message || ""}
        </div>
      )}

      {/* Input Handles */}
      {manifest?.inputs?.map((input, i) => (
        <Handle
          key={`in-${input.name}`}
          type="target"
          position={Position.Left}
          id={input.name}
          style={{ top: 50 + i * 20, background: "#6366f1", width: 8, height: 8 }}
          title={`${input.name} (${input.type})`}
        />
      ))}

      {/* Output Handles */}
      {manifest?.outputs?.map((output, i) => (
        <Handle
          key={`out-${output.name}`}
          type="source"
          position={Position.Right}
          id={output.name}
          style={{ top: 50 + i * 20, background: "#22c55e", width: 8, height: 8 }}
          title={`${output.name} (${output.type})`}
        />
      ))}
    </div>
  );
}

export default memo(AntNode);
