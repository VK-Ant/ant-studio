/* Ant Studio — Results Panel (Bottom) */
import { useWorkflowStore } from "../store/workflowStore";

export default function ResultsPanel() {
  const { lastResult, nodes } = useWorkflowStore();

  if (!lastResult) {
    return (
      <div className="h-36 bg-gray-900 border-t border-gray-800 p-3 overflow-y-auto">
        <p className="text-[10px] text-gray-500">Run a workflow to see results here.</p>
      </div>
    );
  }

  return (
    <div className="h-48 bg-gray-900 border-t border-gray-800 overflow-y-auto">
      <div className="p-2 border-b border-gray-800 flex items-center gap-3">
        <span className="text-xs font-bold text-white">Results</span>
        <span className="text-[10px] text-gray-400">Execution: {lastResult.execution_id?.slice(0, 8)}</span>
      </div>
      <div className="p-2 space-y-1">
        {Object.entries(lastResult.results).map(([nodeId, result]: [string, any]) => {
          const node = nodes.find((n) => n.id === nodeId);
          const label = node?.data?.label || nodeId;
          const statusColor = result.status === "success" ? "text-green-400" : result.status === "error" ? "text-red-400" : "text-gray-400";

          return (
            <div key={nodeId} className="flex items-start gap-2 py-1 border-b border-gray-800/50">
              <span className={`text-[10px] font-mono ${statusColor} w-12 flex-shrink-0`}>
                {result.status === "success" ? "✓" : result.status === "error" ? "✕" : "—"}{" "}
                {result.time_ms?.toFixed(0)}ms
              </span>
              <span className="text-xs text-white font-medium w-32 flex-shrink-0 truncate">{label}</span>
              <span className="text-[10px] text-gray-400 truncate flex-1">{result.message}</span>
              {result.outputs && Object.keys(result.outputs).length > 0 && (
                <details className="text-[10px] text-gray-500">
                  <summary className="cursor-pointer hover:text-gray-300">outputs</summary>
                  <pre className="mt-1 p-1 bg-gray-800 rounded text-[9px] max-h-20 overflow-auto">
                    {JSON.stringify(result.outputs, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
