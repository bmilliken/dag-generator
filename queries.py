# queries.py
from __future__ import annotations
from typing import Iterable, Optional, Tuple, Dict, Any, List
import networkx as nx

# ---------- core queries ----------
def upstream_tables(g: nx.DiGraph, table_id: str) -> set[str]:
    """All ancestors (what table_id depends on)."""
    return nx.ancestors(g, table_id)

def downstream_tables(g: nx.DiGraph, table_id: str) -> set[str]:
    """All descendants (what depends on table_id)."""
    return nx.descendants(g, table_id)
