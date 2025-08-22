# queries.py
from __future__ import annotations
import networkx as nx

def lineage_subgraph(g: nx.DiGraph, table_id: str) -> nx.DiGraph:
    """
    Return an induced DiGraph containing only the tables that actually contribute
    to the columns of the target table, using column-level lineage analysis.
    """
    if table_id not in g:
        raise KeyError(f"Table '{table_id}' not found. Use full 'group.table'.")
    
    # Use column-level lineage if available
    if 'column_graph' in g.graph:
        col_g = g.graph['column_graph']
        
        # Find all columns in the target table
        target_columns = [node for node in col_g.nodes() 
                         if node.startswith(f"{table_id}.")]
        
        # Get all tables that contribute to the target table's columns
        contributing_tables = set([table_id])  # Include the target table itself
        
        for target_col in target_columns:
            # Get all ancestor columns of this target column
            ancestor_columns = nx.ancestors(col_g, target_col)
            
            # Extract unique table IDs from ancestor columns
            for col_id in ancestor_columns:
                parts = col_id.split(".", 2)
                if len(parts) >= 2:
                    ancestor_table = f"{parts[0]}.{parts[1]}"
                    contributing_tables.add(ancestor_table)
        
        # Also include descendants for complete lineage
        descendants = nx.descendants(g, table_id)
        contributing_tables.update(descendants)
        
        # Filter to only include tables that exist in the main graph
        nodes = {t for t in contributing_tables if t in g.nodes()}
        
    else:
        # Fallback to table-level lineage if column graph not available
        nodes = {table_id} | nx.ancestors(g, table_id) | nx.descendants(g, table_id)
    
    return g.subgraph(nodes).copy()
