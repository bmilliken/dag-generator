import { useCallback, useEffect, useState } from "react";
import ReactFlow, { Background, Controls, MiniMap, type Node, type Edge, useNodesState, useEdgesState, Position, MarkerType } from "reactflow";
import "reactflow/dist/style.css";
import { fetchGraph, fetchProjects } from "./api";
import type { GroupedGraphJSON, TableId } from "./types";
import { applyElkLayout } from "./layout";

type Props = { seed?: string };

// Generate distinct colors for groups using HSL color space
function generateGroupColors(groups: string[]): Record<string, string> {
  const colors: Record<string, string> = {};
  const hueStep = 360 / groups.length;
  
  groups.forEach((group, index) => {
    const hue = (index * hueStep) % 360;
    // Use consistent saturation and lightness for pleasant colors
    colors[group] = `hsl(${hue}, 65%, 85%)`;
  });
  
  return colors;
}

function buildNodesAndEdges(data: GroupedGraphJSON) {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  const seen = new Set<string>();
  
  // Extract all unique groups and generate colors
  const groups = data.map(g => g.group);
  const groupColors = generateGroupColors(groups);

  for (const group of data) {
    for (const tbl of group.tables) {
      const id = `${group.group}.${tbl.name}`;
      if (!seen.has(id)) {
        nodes.push({
          id,
          data: { label: tbl.name, group: group.group },
          position: { x: 0, y: 0 },
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
          style: { 
            padding: 12, 
            borderRadius: 8, 
            border: "2px solid #333", 
            background: groupColors[group.group],
            fontSize: 12,
            fontWeight: 'bold',
            minWidth: '140px',
            maxWidth: '200px',
            textAlign: 'center',
            wordWrap: 'break-word',
            whiteSpace: 'normal',
            lineHeight: '1.2'
          }
        });
        seen.add(id);
      }
    }
  }

  for (const group of data) {
    for (const tbl of group.tables) {
      const targetId = `${group.group}.${tbl.name}`;
      for (const dep of tbl.dependencies) {
        edges.push({ 
          id: `${dep}->${targetId}`, 
          source: dep, 
          target: targetId,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20,
            color: '#333',
          },
          style: {
            strokeWidth: 2,
            stroke: '#333',
          }
        });
      }
    }
  }
  return { nodes, edges, groupColors };
}

export default function GraphView({ seed }: Props) {
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [groupColors, setGroupColors] = useState<Record<string, string>>({});
  
  // Project selection state
  const [availableProjects, setAvailableProjects] = useState<string[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("ecommerce"); // Default project

  const load = useCallback(async (project?: string) => {
    const projectToUse = project || selectedProject;
    if (!projectToUse) return;
    
    setLoading(true);
    setErr(null);
    try {
      const data = await fetchGraph(projectToUse, seed);
      const { nodes, edges, groupColors } = buildNodesAndEdges(data);
      const positioned = await applyElkLayout(nodes, edges);
      setNodes(positioned);
      setEdges(edges);
      setGroupColors(groupColors);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
      setNodes([]);
      setEdges([]);
      setGroupColors({});
    } finally {
      setLoading(false);
    }
  }, [seed, setNodes, setEdges, selectedProject]);

  // Load available projects on mount
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const projects = await fetchProjects();
        setAvailableProjects(projects);
        // If default project doesn't exist, use first available
        if (projects.length > 0 && !projects.includes("ecommerce")) {
          setSelectedProject(projects[0]);
        }
      } catch (e) {
        console.error("Failed to load projects:", e);
      }
    };
    loadProjects();
  }, []);

  useEffect(() => { load(); }, [load]);

  // Reload when selected project changes
  useEffect(() => {
    if (selectedProject) {
      load();
    }
  }, [selectedProject, load]);

  const [active, setActive] = useState<TableId | null>(null);
  const [lineageNodes, setLineageNodes] = useState<Set<TableId> | null>(null);
  const [lineageEdges, setLineageEdges] = useState<Set<string> | null>(null);

  const loadLineage = useCallback(async (tableId: TableId) => {
    setLoading(true);
    setErr(null);
    try {
      // Fetch lineage data from backend
      const lineageData = await fetchGraph(selectedProject, tableId);
      const { nodes: lineageNodeList, edges: lineageEdgeList } = buildNodesAndEdges(lineageData);
      
      // Convert to sets for quick lookup
      const nodeSet = new Set(lineageNodeList.map(n => n.id));
      const edgeSet = new Set(lineageEdgeList.map(e => e.id));
      
      setLineageNodes(nodeSet);
      setLineageEdges(edgeSet);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
      setLineageNodes(null);
      setLineageEdges(null);
    } finally {
      setLoading(false);
    }
  }, [selectedProject]);

  const handleNodeClick = useCallback((nodeId: TableId) => {
    setActive(nodeId);
    loadLineage(nodeId);
  }, [loadLineage]);

  const clearHighlight = useCallback(() => {
    setActive(null);
    setLineageNodes(null);
    setLineageEdges(null);
  }, []);

  const handleProjectChange = useCallback((newProject: string) => {
    setSelectedProject(newProject);
    clearHighlight(); // Clear any active highlights when switching projects
  }, [clearHighlight]);

  const handleReload = useCallback(() => {
    load();
  }, [load]);

  const rfNodes = nodes.map((n) => ({
    ...n,
    style: { ...n.style, opacity: lineageNodes ? (lineageNodes.has(n.id) ? 1 : 0.25) : 1, boxShadow: active === n.id ? "0 0 0 2px #2563eb" : "none" }
  }));

  const rfEdges = edges.map((e) => ({
    ...e,
    style: { opacity: lineageEdges ? (lineageEdges.has(e.id) ? 1 : 0.2) : 1 },
    animated: !!(active && lineageEdges?.has(e.id))
  }));

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      {/* Hide ReactFlow handles (connection dots) */}
      <style>{`
        .react-flow__handle {
          opacity: 0 !important;
          pointer-events: none !important;
        }
      `}</style>
      
      <div style={{ position: "absolute", zIndex: 10, left: 12, top: 12, display: "flex", gap: 8, alignItems: "center" }}>
        {/* Project Selector */}
        <select 
          value={selectedProject} 
          onChange={(e) => handleProjectChange(e.target.value)}
          style={{ 
            padding: "6px 10px", 
            borderRadius: 8, 
            border: "1px solid #ddd", 
            background: "#fff",
            fontSize: 14
          }}
        >
          {availableProjects.map(project => (
            <option key={project} value={project}>
              {project}
            </option>
          ))}
        </select>
        
        <button onClick={clearHighlight} disabled={!active} style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid #ddd", background: "#fff" }}>
          Clear highlight
        </button>
        <button onClick={handleReload} style={{ padding: "6px 10px", borderRadius: 8, border: "1px solid #ddd", background: "#fff" }}>
          Reload
        </button>
        {loading && <span>Loading…</span>}
        {err && <span style={{ color: "crimson" }}>{err}</span>}
      </div>

      {/* Dynamic Legend */}
      {Object.keys(groupColors).length > 0 && (
        <div style={{ 
          position: "absolute", 
          zIndex: 10, 
          right: 12, 
          top: 12, 
          background: "rgba(255,255,255,0.95)",
          padding: 12,
          borderRadius: 8,
          border: "1px solid #ddd",
          fontSize: 12,
          maxWidth: 200
        }}>
          <div style={{ fontWeight: 'bold', marginBottom: 8 }}>Groups</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {Object.entries(groupColors).map(([group, color]) => (
              <div key={group} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ 
                  width: 16, 
                  height: 16, 
                  background: color, 
                  border: '2px solid #333', 
                  borderRadius: 3 
                }}></div>
                <span>{group}</span>
              </div>
            ))}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4, paddingTop: 4, borderTop: '1px solid #eee' }}>
              <span>→</span>
              <span>Data flows left to right</span>
            </div>
          </div>
        </div>
      )}

      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, n) => handleNodeClick(n.id as TableId)}
        fitView
      >
        <MiniMap pannable zoomable />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}
