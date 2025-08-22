from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Dict, Any

import networkx as nx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from loader import load_all_specs
from graph_builder import build_graph
from queries import lineage_subgraph
from json_export import graph_to_grouped_json

# ----- App setup -----
app = FastAPI(title="DAG JSON API", version="0.1.0")

# (Optional) allow a local frontend to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Single, global graph stored in app state
@app.on_event("startup")
def _build_graph_on_startup() -> None:
    specs = load_all_specs(Path("../Tables"))
    g: nx.DiGraph = build_graph(specs)
    app.state.graph = g

@app.get("/healthz")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/reload")
def reload_graph() -> Dict[str, str]:
    """Reload specs and rebuild the in-memory graph (handy during dev)."""
    specs = load_all_specs(Path("../Tables"))
    g: nx.DiGraph = build_graph(specs)
    app.state.graph = g
    return {"status": "reloaded"}

@app.get("/graph")
def get_graph(seed: Optional[str] = Query(default=None, description="Fully-qualified 'group.table'")) -> List[Dict[str, Any]]:
    """
    Return the grouped MVP JSON for:
      - the whole graph (if seed is not provided)
      - the lineage subgraph connected to the seed (ancestors ∪ seed ∪ descendants)
    """
    g: nx.DiGraph = app.state.graph
    if seed:
        if seed not in g.nodes:
            raise HTTPException(status_code=404, detail=f"Table '{seed}' not found. Use full 'group.table'.")
        g = lineage_subgraph(g, seed)

    return graph_to_grouped_json(g)
