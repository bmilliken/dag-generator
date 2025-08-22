
import type { Edge, Node } from "reactflow";

// Simple topological sort to create left-to-right layout
function topologicalSort(nodes: Node[], edges: Edge[]): Map<string, number> {
  const inDegree = new Map<string, number>();
  const outgoing = new Map<string, string[]>();
  const layers = new Map<string, number>();
  
  // Initialize
  nodes.forEach(node => {
    inDegree.set(node.id, 0);
    outgoing.set(node.id, []);
  });
  
  // Build graph
  edges.forEach(edge => {
    const current = inDegree.get(edge.target) || 0;
    inDegree.set(edge.target, current + 1);
    
    const targets = outgoing.get(edge.source) || [];
    targets.push(edge.target);
    outgoing.set(edge.source, targets);
  });
  
  // Topological sort with layer assignment
  const queue: string[] = [];
  const processed = new Set<string>();
  
  // Start with nodes that have no dependencies (source tables)
  nodes.forEach(node => {
    if ((inDegree.get(node.id) || 0) === 0) {
      queue.push(node.id);
      layers.set(node.id, 0);
    }
  });
  
  while (queue.length > 0) {
    const current = queue.shift()!;
    if (processed.has(current)) continue;
    processed.add(current);
    
    const currentLayer = layers.get(current) || 0;
    const targets = outgoing.get(current) || [];
    
    targets.forEach(target => {
      const newInDegree = (inDegree.get(target) || 0) - 1;
      inDegree.set(target, newInDegree);
      
      // Set target to be at least one layer deeper than current
      const targetLayer = Math.max(layers.get(target) || 0, currentLayer + 1);
      layers.set(target, targetLayer);
      
      if (newInDegree === 0) {
        queue.push(target);
      }
    });
  }
  
  return layers;
}

export async function applyElkLayout(nodes: Node[], edges: Edge[]) {
  // First, calculate layers using topological sort
  const layers = topologicalSort(nodes, edges);
  
  // Group nodes by layer
  const nodesByLayer = new Map<number, Node[]>();
  nodes.forEach(node => {
    const layer = layers.get(node.id) || 0;
    if (!nodesByLayer.has(layer)) {
      nodesByLayer.set(layer, []);
    }
    nodesByLayer.get(layer)!.push(node);
  });
  
  // Position nodes left-to-right by layer
  const layerWidth = 250; // Horizontal spacing between layers
  const nodeHeight = 100; // Vertical spacing between nodes
  const startX = 50;
  const startY = 50;
  
  const positions = new Map<string, { x: number; y: number }>();
  
  Array.from(nodesByLayer.keys()).sort((a, b) => a - b).forEach(layerNum => {
    const layerNodes = nodesByLayer.get(layerNum)!;
    const x = startX + layerNum * layerWidth;
    
    layerNodes.forEach((node, index) => {
      const y = startY + index * nodeHeight;
      positions.set(node.id, { x, y });
    });
  });

  return nodes.map((n) => ({ 
    ...n, 
    position: positions.get(n.id) ?? { x: 0, y: 0 } 
  }));
}
