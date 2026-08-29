/* Ant Studio — Toolbar */
import { useState, useEffect } from "react";
import { useWorkflowStore } from "../store/workflowStore";
import { useExecution } from "../hooks/useExecution";
import { fetchTemplates, loadTemplate, saveWorkflow } from "../api/client";

export default function Toolbar() {
  const { isExecuting, toWorkflowJSON, loadWorkflow, manifests, clearCanvas } = useWorkflowStore();
  const { execute, cancel } = useExecution();
  const [templates, setTemplates] = useState<{ name: string; file: string; description: string }[]>([]);
  const [showTemplates, setShowTemplates] = useState(false);

  useEffect(() => {
    fetchTemplates().then(setTemplates).catch(() => {});
  }, []);

  const handleSave = async () => {
    const wf = toWorkflowJSON();
    const name = prompt("Workflow name:", "My Workflow");
    if (name) {
      wf.name = name;
      const result = await saveWorkflow(wf);
      alert(`Saved: ${result.saved}`);
    }
  };

  const handleLoadTemplate = async (file: string) => {
    const wf = await loadTemplate(file);
    loadWorkflow(wf, manifests);
    setShowTemplates(false);
  };

  return (
    <div className="h-12 bg-gray-900 border-b border-gray-800 flex items-center px-4 gap-3">
      {/* Logo */}
      <div className="flex items-center gap-2 mr-4">
        <span className="text-lg font-bold text-ant-red">ANT</span>
        <span className="text-lg font-light text-white">Studio</span>
      </div>

      <div className="h-6 w-px bg-gray-700" />

      {/* Run / Cancel */}
      {isExecuting ? (
        <button onClick={cancel} className="px-4 py-1.5 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded transition-colors">
          Cancel
        </button>
      ) : (
        <button onClick={execute} className="px-4 py-1.5 bg-green-600 hover:bg-green-500 text-white text-xs font-bold rounded transition-colors flex items-center gap-1">
          ▶ Run
        </button>
      )}

      {/* Save */}
      <button onClick={handleSave} className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded transition-colors">
        Save
      </button>

      {/* Templates */}
      <div className="relative">
        <button
          onClick={() => setShowTemplates(!showTemplates)}
          className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded transition-colors"
        >
          Templates
        </button>
        {showTemplates && (
          <div className="absolute top-10 left-0 w-64 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50">
            {templates.length === 0 ? (
              <p className="p-3 text-xs text-gray-400">No templates found</p>
            ) : (
              templates.map((t) => (
                <button
                  key={t.file}
                  onClick={() => handleLoadTemplate(t.file)}
                  className="w-full text-left px-3 py-2 hover:bg-gray-700 transition-colors border-b border-gray-700 last:border-b-0"
                >
                  <p className="text-xs font-semibold text-white">{t.name}</p>
                  <p className="text-[10px] text-gray-400">{t.description}</p>
                </button>
              ))
            )}
          </div>
        )}
      </div>

      {/* Clear */}
      <button onClick={clearCanvas} className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded transition-colors">
        Clear
      </button>

      {/* Spacer + Status */}
      <div className="flex-1" />
      <span className="text-[10px] text-gray-500">
        {isExecuting ? "Executing..." : "Ready"} | {manifests.length} nodes available
      </span>
    </div>
  );
}
