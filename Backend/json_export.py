# json_export.py
from __future__ import annotations
from collections import defaultdict
from typing import Dict, List
import networkx as nx

def _group_and_name(node_id: str, attrs: dict) -> tuple[str, str]:
    """Derive (group, table_name) from node attrs or fallback by splitting the id."""
    g = attrs.get("group")
    t = attrs.get("table")
    if (g is None or t is None) and "." in node_id:
        grp, _, rest = node_id.partition(".")
        g = g if g is not None else grp
        t = t if t is not None else (rest or node_id)
    return g or "", t or node_id

def graph_to_grouped_json(g: nx.DiGraph) -> List[Dict]:
    """
    Export DiGraph -> MVP JSON:
    [
      { "group": "<group>",
        "tables": [
          { "name": "<table>", "dependencies": ["group.table", ...] }
        ]
      },
      ...
    ]
    Dependencies are the node's direct upstream predecessors within `g`.
    """
    grouped: Dict[str, Dict[str, List[str]]] = defaultdict(dict)

    # Build node -> deps
    for node_id, attrs in g.nodes(data=True):
        grp, tbl = _group_and_name(node_id, attrs or {})
        deps = sorted(str(p) for p in g.predecessors(node_id) if p in g)  # fully-qualified ids
        grouped[grp][tbl] = deps

    # Emit sorted, stable result
    out: List[Dict] = []
    for grp in sorted(grouped.keys()):
        tables = [{"name": tbl, "dependencies": grouped[grp][tbl]}
                  for tbl in sorted(grouped[grp].keys())]
        out.append({"group": grp, "tables": tables})
    return out
