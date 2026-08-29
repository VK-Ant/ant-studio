/* Ant Studio — Main App */
import { useEffect } from "react";
import { useWorkflowStore } from "./store/workflowStore";
import { fetchNodes } from "./api/client";
import Toolbar from "./components/Toolbar";
import NodePalette from "./components/NodePalette";
import Canvas from "./components/Canvas";
import PropertiesPanel from "./components/PropertiesPanel";
import ResultsPanel from "./components/ResultsPanel";

export default function App() {
  const { setManifests } = useWorkflowStore();

  useEffect(() => {
    fetchNodes()
      .then(setManifests)
      .catch((e) => console.error("Failed to fetch nodes:", e));
  }, [setManifests]);

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-white overflow-hidden">
      <Toolbar />
      <div className="flex-1 flex overflow-hidden">
        <NodePalette />
        <div className="flex-1 flex flex-col">
          <Canvas />
          <ResultsPanel />
        </div>
        <PropertiesPanel />
      </div>
    </div>
  );
}
