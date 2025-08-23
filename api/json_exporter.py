"""
DAG JSON Exporter

This module provides minimal JSON export capabilities for the assembled DAG structure.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import Dict, List, Any
from objects import Group, Table, Column


class JSONExporter:
    """
    Minimal JSON exporter for DAG structure.
    """
    
    def __init__(self, groups: Dict[str, Group], tables: Dict[str, Table], columns: Dict[str, Column]):
        self.groups = groups
        self.tables = tables
        self.columns = columns
    
    
    def to_json(self) -> Dict[str, Any]:
        """Export complete DAG structure as JSON."""
        # Build groups and tables from all tables
        groups_dict = {}
        for table in self.tables.values():
            if table.group not in groups_dict:
                groups_dict[table.group] = []
            if table.name not in groups_dict[table.group]:  # Avoid duplicates
                groups_dict[table.group].append(table.name)
        
        # Build groups list
        groups = [
            {
                "group": group_name,
                "tables": sorted(table_names)
            }
            for group_name, table_names in sorted(groups_dict.items())
        ]
        
        # Build edges (connections)
        edges = []
        for table in self.tables.values():
            for dep in table.dependencies:
                edges.append({
                    "from": dep.get_full_name(),
                    "to": table.get_full_name()
                })
        
        return {
            "groups": groups,
            "connections": sorted(edges, key=lambda x: (x["from"], x["to"]))
        }
    
    def export_to_file(self, filepath: str) -> None:
        """Save JSON to file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_json(), f, indent=2)
    
    def to_json_string(self) -> str:
        """Return JSON as formatted string."""
        return json.dumps(self.to_json(), indent=2)
    
    def table_lineage_json(self, table_name: str) -> Dict[str, Any]:
        """Export complete lineage for a single table including tables, connections, and column details."""
        # Handle both full names (group.table) and just table names
        table = None
        table_key = None
        
        if table_name in self.tables:
            # Direct match (full name like 'stg.enriched_orders')
            table = self.tables[table_name]
            table_key = table_name
        else:
            # Try to find by table name only
            for key, tbl in self.tables.items():
                if tbl.name == table_name:
                    table = tbl
                    table_key = key
                    break
        
        if table is None:
            return {"error": f"Table '{table_name}' not found"}
        
        # Collect all related tables (including ultimate sources and targets)
        related_tables = set([table])
        
        # Add all ultimate source tables (recursively)
        def add_sources(t):
            for dep in t.dependencies:
                if dep not in related_tables:
                    related_tables.add(dep)
                    add_sources(dep)  # Recursively add sources
        
        # Add all ultimate target tables (recursively)  
        def add_targets(t):
            for dep in t.dependents:
                if dep not in related_tables:
                    related_tables.add(dep)
                    add_targets(dep)  # Recursively add targets
        
        add_sources(table)
        add_targets(table)
        
        # Group related tables by group name
        groups_dict = {}
        for t in related_tables:
            if t.group not in groups_dict:
                groups_dict[t.group] = []
            groups_dict[t.group].append(t.name)
        
        # Build groups list
        groups = [
            {
                "group": group_name,
                "tables": sorted(table_names)
            }
            for group_name, table_names in sorted(groups_dict.items())
        ]
        
        # Build ALL connections involving any of the related tables
        connections = []
        for t in related_tables:
            for dep in t.dependencies:
                if dep in related_tables:  # Only include connections between related tables
                    connections.append({
                        "from": dep.get_full_name(),
                        "to": t.get_full_name()
                    })
        
        # Build column lineage information for the target table
        columns_info = []
        for column in table.columns:
            # Get immediate dependencies
            immediate_dependencies = column.get_prev_columns()
            immediate_deps_info = [
                {
                    "full_path": dep_col.get_full_name(),
                    "description": dep_col.description
                }
                for dep_col in sorted(immediate_dependencies, key=lambda c: c.get_full_name())
            ]
            
            # Get ultimate source columns
            source_columns = column.get_source_columns()
            source_info = [
                {
                    "full_path": src_col.get_full_name(),
                    "description": src_col.description
                }
                for src_col in sorted(source_columns, key=lambda c: c.get_full_name())
            ]
            
            column_info = {
                "column": {
                    "full_path": column.get_full_name(),
                    "description": column.description,
                    "immediate_dependencies": immediate_deps_info,
                    "source_columns": source_info
                }
            }
            
            columns_info.append(column_info)
        
        return {
            "target_table": table.get_full_name(),
            "groups": groups,
            "connections": sorted(connections, key=lambda x: (x["from"], x["to"])),
            "columns_lineage": sorted(columns_info, key=lambda x: x["column"]["full_path"])
        }
    
    def table_lineage_json_string(self, table_name: str) -> str:
        """Return complete table lineage JSON as formatted string."""
        return json.dumps(self.table_lineage_json(table_name), indent=2)
