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

# Project graphs stored in app state
@app.on_event("startup")
def _build_graphs_on_startup() -> None:
    app.state.graphs = {}
    projects_path = Path("../Projects")
    if projects_path.exists():
        for project_dir in projects_path.iterdir():
            if project_dir.is_dir():
                try:
                    specs = load_all_specs(project_dir)
                    g: nx.DiGraph = build_graph(specs)
                    app.state.graphs[project_dir.name] = g
                except Exception as e:
                    print(f"Failed to load project {project_dir.name}: {e}")

@app.get("/projects")
def get_projects() -> List[str]:
    """Return list of available projects."""
    return list(app.state.graphs.keys())

@app.get("/healthz")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/reload")
def reload_graphs() -> Dict[str, str]:
    """Reload specs and rebuild all project graphs (handy during dev)."""
    app.state.graphs = {}
    projects_path = Path("../Projects")
    if projects_path.exists():
        for project_dir in projects_path.iterdir():
            if project_dir.is_dir():
                try:
                    specs = load_all_specs(project_dir)
                    g: nx.DiGraph = build_graph(specs)
                    app.state.graphs[project_dir.name] = g
                except Exception as e:
                    print(f"Failed to reload project {project_dir.name}: {e}")
    return {"status": "reloaded"}

@app.get("/graph")
def get_graph(
    project: str = Query(default="ecommerce", description="Project name"),
    seed: Optional[str] = Query(default=None, description="Fully-qualified 'group.table'")
) -> List[Dict[str, Any]]:
    """
    Return the grouped MVP JSON for:
      - the whole graph (if seed is not provided)
      - the lineage subgraph connected to the seed (ancestors ∪ seed ∪ descendants)
    """
    if project not in app.state.graphs:
        raise HTTPException(status_code=404, detail=f"Project '{project}' not found")
    
    g: nx.DiGraph = app.state.graphs[project]
    if seed:
        if seed not in g.nodes:
            raise HTTPException(status_code=404, detail=f"Table '{seed}' not found. Use full 'group.table'.")
        g = lineage_subgraph(g, seed)

    return graph_to_grouped_json(g)
