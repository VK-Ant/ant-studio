/* Ant Studio — Node Palette (Left Panel) */
import { useWorkflowStore } from "../store/workflowStore";
import type { NodeManifest } from "../types";

const categoryOrder = ["common", "document", "backbone", "output"];
const categoryColors: Record<string, string> = {
  common: "text-gray-400",
  document: "text-blue-400",
  backbone: "text-orange-400",
  output: "text-green-400",
};

export default function NodePalette() {
  const { manifests, addNode } = useWorkflowStore();

  const grouped: Record<string, NodeManifest[]> = {};
  manifests.forEach((m) => {
    grouped[m.category] = grouped[m.category] || [];
    grouped[m.category].push(m);
  });

  const handleDragStart = (e: React.DragEvent, manifest: NodeManifest) => {
    e.dataTransfer.setData("application/antstudio-node", JSON.stringify(manifest));
    e.dataTransfer.effectAllowed = "move";
  };

  const handleClick = (manifest: NodeManifest) => {
    addNode(manifest, { x: 200 + Math.random() * 300, y: 100 + Math.random() * 300 });
  };

  return (
    <div className="w-56 bg-gray-900 border-r border-gray-800 overflow-y-auto flex flex-col">
      <div className="p-3 border-b border-gray-800">
        <h2 className="text-sm font-bold text-white tracking-wider">NODES</h2>
      </div>

      {categoryOrder.map((cat) =>
        grouped[cat] ? (
          <div key={cat} className="px-2 py-2">
            <h3 className={`text-[10px] font-bold tracking-widest uppercase mb-1 px-1 ${categoryColors[cat] || "text-gray-400"}`}>
              {cat}
            </h3>
            {grouped[cat].map((m) => (
              <div
                key={m.node_type}
                draggable
                onDragStart={(e) => handleDragStart(e, m)}
                onClick={() => handleClick(m)}
                className="flex items-center gap-2 px-2 py-1.5 rounded cursor-grab hover:bg-gray-800 active:cursor-grabbing transition-colors mb-0.5"
                title={m.description}
              >
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: m.color }} />
                <span className="text-xs text-gray-300 truncate">{m.label}</span>
              </div>
            ))}
          </div>
        ) : null
      )}
    </div>
  );
}
