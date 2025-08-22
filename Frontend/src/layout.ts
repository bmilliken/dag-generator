
import ELK, { type ElkNode, type LayoutOptions } from "elkjs/lib/elk.bundled.js";
import type { Edge, Node } from "reactflow";

const elk = new ELK();
const options: LayoutOptions = {
  "elk.algorithm": "layered",
  "elk.direction": "RIGHT",
  "elk.layered.spacing.nodeNodeBetweenLayers": "120",
  "elk.spacing.nodeNode": "60",
  "elk.edgeRouting": "ORTHOGONAL",
  "elk.layered.nodePlacement.strategy": "NETWORK_SIMPLEX",
  "elk.layered.crossingMinimization.strategy": "LAYER_SWEEP"
};

export async function applyElkLayout(nodes: Node[], edges: Edge[]) {
  // Group nodes by their group property to enforce layer ordering
  const nodesByGroup = new Map<string, Node[]>();
  nodes.forEach(node => {
    const group = node.data?.group || 'unknown';
    if (!nodesByGroup.has(group)) {
      nodesByGroup.set(group, []);
    }
    nodesByGroup.get(group)!.push(node);
  });

  // Define expected group order (you can adjust this)
  const groupOrder = ['src', 'stg', 'int', 'mart'];
  
  const elkGraph: ElkNode = {
    id: "root",
    layoutOptions: options,
    children: nodes.map((n) => {
      const group = n.data?.group || 'unknown';
      const groupIndex = groupOrder.indexOf(group);
      
      const baseNode = {
        id: n.id,
        width: 200,
        height: 60
      };
      
      // Add layer constraint if group is recognized
      if (groupIndex >= 0) {
        return {
          ...baseNode,
          layoutOptions: {
            "elk.layered.layering.layerChoiceConstraint": groupIndex.toString()
          } as LayoutOptions
        };
      }
      
      return baseNode;
    }),
    edges: edges.map((e) => ({ id: e.id, sources: [e.source], targets: [e.target] }))
  };

  const res = await elk.layout(elkGraph);
  const pos = new Map<string, { x: number; y: number }>();
  res.children?.forEach((c) => {
    if (c.x !== undefined && c.y !== undefined) pos.set(c.id, { x: c.x, y: c.y });
  });

  return nodes.map((n) => ({ ...n, position: pos.get(n.id) ?? { x: 0, y: 0 } }));
}
