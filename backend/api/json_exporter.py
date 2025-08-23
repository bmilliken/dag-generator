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
        
        # Collect all tables connected to this table through column dependencies and dependents
        connected_tables = set()
        
        # Build column lineage information for the target table
        columns_info = []
        for column in table.columns:
            # Get all columns connected to this column (dependencies and dependents)
            all_connected_columns = column.get_all_connected_columns()
            
            # Add tables from all connected columns to our set
            for connected_col in all_connected_columns:
                connected_tables.add(connected_col.table)
            
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
        
        # Add the target table itself to the connected tables
        connected_tables.add(table)
        
        # Build connections between all connected tables
        connections = []
        for connected_table in connected_tables:
            for dep_table in connected_table.dependencies:
                if dep_table in connected_tables:  # Only include connections between tables in our set
                    connections.append({
                        "from": dep_table.get_full_name(),
                        "to": connected_table.get_full_name()
                    })
        
        # Group connected tables by group name for groups output
        groups_dict = {}
        for connected_table in connected_tables:
            if connected_table.group not in groups_dict:
                groups_dict[connected_table.group] = []
            groups_dict[connected_table.group].append(connected_table.name)
        
        # Build groups list
        groups = [
            {
                "group": group_name,
                "tables": sorted(table_names)
            }
            for group_name, table_names in sorted(groups_dict.items())
        ]
        
        return {
            "target_table": table.get_full_name(),
            "groups": groups,
            "connections": sorted(connections, key=lambda x: (x["from"], x["to"])),
            "columns_lineage": sorted(columns_info, key=lambda x: x["column"]["full_path"])
        }
    
    def table_lineage_json_string(self, table_name: str) -> str:
        """Return complete table lineage JSON as formatted string."""
        return json.dumps(self.table_lineage_json(table_name), indent=2)
