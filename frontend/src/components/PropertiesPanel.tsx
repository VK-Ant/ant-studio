/* Ant Studio — Properties Panel (Right Panel) */
import { useWorkflowStore } from "../store/workflowStore";

export default function PropertiesPanel() {
  const { nodes, selectedNodeId, updateNodeConfig, removeNode } = useWorkflowStore();
  const selected = nodes.find((n) => n.id === selectedNodeId);

  if (!selected) {
    return (
      <div className="w-64 bg-gray-900 border-l border-gray-800 p-4 flex items-center justify-center">
        <p className="text-gray-500 text-xs">Select a node to configure</p>
      </div>
    );
  }

  const { data } = selected;
  const manifest = data.manifest;

  return (
    <div className="w-64 bg-gray-900 border-l border-gray-800 overflow-y-auto">
      {/* Header */}
      <div className="p-3 border-b border-gray-800">
        <h3 className="text-sm font-bold text-white">{data.label}</h3>
        <p className="text-[10px] text-gray-400 mt-0.5">{manifest?.description}</p>
      </div>

      {/* Config Fields */}
      <div className="p-3 space-y-3">
        {manifest?.config?.map((cfg) => (
          <div key={cfg.key}>
            <label className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
              {cfg.label}
            </label>
            {cfg.type === "select" ? (
              <select
                value={data.config[cfg.key] ?? cfg.default}
                onChange={(e) => updateNodeConfig(selected.id, cfg.key, e.target.value)}
                className="w-full mt-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white"
              >
                {cfg.options?.map((o) => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>
            ) : cfg.type === "boolean" ? (
              <div className="mt-1">
                <input
                  type="checkbox"
                  checked={data.config[cfg.key] ?? cfg.default}
                  onChange={(e) => updateNodeConfig(selected.id, cfg.key, e.target.checked)}
                  className="mr-2"
                />
                <span className="text-xs text-gray-300">{data.config[cfg.key] ? "Enabled" : "Disabled"}</span>
              </div>
            ) : cfg.type === "number" ? (
              <input
                type="number"
                value={data.config[cfg.key] ?? cfg.default}
                min={cfg.min}
                max={cfg.max}
                step={0.1}
                onChange={(e) => updateNodeConfig(selected.id, cfg.key, parseFloat(e.target.value))}
                className="w-full mt-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white"
              />
            ) : cfg.type === "text_area" ? (
              <textarea
                value={data.config[cfg.key] ?? cfg.default}
                onChange={(e) => updateNodeConfig(selected.id, cfg.key, e.target.value)}
                rows={3}
                className="w-full mt-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white resize-y"
              />
            ) : (
              <input
                type="text"
                value={data.config[cfg.key] ?? cfg.default}
                onChange={(e) => updateNodeConfig(selected.id, cfg.key, e.target.value)}
                className="w-full mt-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white"
              />
            )}
          </div>
        ))}
      </div>

      {/* Node Info */}
      <div className="p-3 border-t border-gray-800">
        <div className="text-[10px] text-gray-500 space-y-0.5">
          <p>Type: {data.node_type}</p>
          <p>Inputs: {manifest?.inputs?.length || 0} | Outputs: {manifest?.outputs?.length || 0}</p>
          {data.status && data.status !== "idle" && (
            <p className={data.status === "success" ? "text-green-400" : data.status === "error" ? "text-red-400" : "text-blue-400"}>
              Status: {data.status} {data.timeMs ? `(${data.timeMs.toFixed(0)}ms)` : ""}
            </p>
          )}
          {data.message && <p className="text-gray-400 truncate">{data.message}</p>}
        </div>
        <button
          onClick={() => removeNode(selected.id)}
          className="mt-3 w-full text-xs text-red-400 hover:text-red-300 border border-red-900 hover:border-red-700 rounded py-1 transition-colors"
        >
          Remove Node
        </button>
      </div>
    </div>
  );
}
