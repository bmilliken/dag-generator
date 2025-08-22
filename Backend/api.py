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

@app.get("/table-details")
def get_table_details(
    project: str = Query(default="ecommerce", description="Project name"),
    table: str = Query(description="Fully-qualified 'group.table' to get details for")
) -> Dict[str, Any]:
    """
    Return detailed column-level dependency information for a specific table.
    """
    if project not in app.state.graphs:
        raise HTTPException(status_code=404, detail=f"Project '{project}' not found")
    
    g: nx.DiGraph = app.state.graphs[project]
    
    if table not in g.nodes:
        raise HTTPException(status_code=404, detail=f"Table '{table}' not found")
    
    # Get the column graph
    col_g = g.graph.get('column_graph')
    if not col_g:
        return {"table": table, "columns": [], "source_tables": []}
    
    # Find all columns in the target table
    target_columns = [node for node in col_g.nodes() if node.startswith(f"{table}.")]
    
    column_details = []
    all_source_tables = set()
    
    for col_node in target_columns:
        col_name = col_node.split(".", 2)[-1]  # Extract column name
        
        # Get direct dependencies for this column
        direct_deps = list(col_g.predecessors(col_node))
        
        # Get all transitive dependencies (source columns)
        transitive_deps = nx.ancestors(col_g, col_node)
        
        # Group transitive dependencies by source table
        source_columns = {}
        for dep_col in transitive_deps:
            parts = dep_col.split(".", 2)
            if len(parts) >= 2:
                dep_table = f"{parts[0]}.{parts[1]}"
                dep_col_name = parts[2] if len(parts) > 2 else ""
                
                # Only include source tables (tables with no dependencies for their columns)
                if col_g.in_degree(dep_col) == 0:  # This is a source column
                    if dep_table not in source_columns:
                        source_columns[dep_table] = []
                    source_columns[dep_table].append(dep_col_name)
                    all_source_tables.add(dep_table)
        
        column_details.append({
            "column": col_name,
            "direct_dependencies": direct_deps,
            "source_columns": source_columns
        })
    
    return {
        "table": table,
        "columns": column_details,
        "source_tables": sorted(list(all_source_tables))
    }
