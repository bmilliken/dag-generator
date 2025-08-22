# queries.py
from __future__ import annotations
import networkx as nx

def lineage_subgraph(g: nx.DiGraph, table_id: str) -> nx.DiGraph:
    """
    Return an induced DiGraph containing:
      ancestors(table_id) ∪ {table_id} ∪ descendants(table_id).
    The returned graph is a COPY so you can modify it safely.
    """
    if table_id not in g:
        raise KeyError(f"Table '{table_id}' not found. Use full 'group.table'.")
    nodes = {table_id} | nx.ancestors(g, table_id) | nx.descendants(g, table_id)
    return g.subgraph(nodes).copy()
