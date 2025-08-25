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
        
        # Collect all tables in the lineage of this table (without cross-contamination)
        connected_tables = set()
        
        # Build column lineage information for the target table
        columns_info = []
        
        # Collect all lineage tables including from invisible columns
        # Don't filter invisible columns here - let them participate fully in lineage calculation
        for column in table.columns:
            # Get columns in the lineage of this column (prevents cross-contamination)
            lineage_columns = column.get_lineage_columns()
            
            # Add tables from all lineage columns to our set (including from invisible columns)
            for lineage_col in lineage_columns:
                connected_tables.add(lineage_col.table)
        
        # Build column info only for visible columns (filter invisible columns only for frontend display)
        for column in table.columns:
            # Skip invisible columns in the final output - they are only for internal lineage tracking
            if column.is_invisible:
                continue
                
            # Get immediate dependencies
            immediate_dependencies = column.get_prev_columns()
            immediate_deps_info = [
                {
                    "full_path": dep_col.get_full_name(),
                    "description": dep_col.description,
                    "key_type": dep_col.key_type
                }
                for dep_col in sorted(immediate_dependencies, key=lambda c: c.get_full_name())
                if not dep_col.is_invisible  # Filter invisible columns from user-visible dependency info
            ]
            
            # Get ultimate source columns
            source_columns = column.get_source_columns()
            source_info = [
                {
                    "full_path": src_col.get_full_name(),
                    "description": src_col.description,
                    "key_type": src_col.key_type
                }
                for src_col in sorted(source_columns, key=lambda c: c.get_full_name())
                if not src_col.is_invisible  # Filter invisible columns from user-visible source info
            ]
            
            # Determine if this column is a source column (no immediate dependencies)
            is_source_column = len(immediate_dependencies) == 0
            
            column_info = {
                "column": {
                    "full_path": column.get_full_name(),
                    "description": column.description,
                    "key_type": column.key_type,
                    "is_source_column": is_source_column
                }
            }
            
            # If it's a source column, we don't need immediate_dependencies or source_columns
            # since they would be empty or just reference itself
            if is_source_column:
                # For source columns, we only include the basic info with the flag
                pass  # column_info already has what we need
            else:
                # For non-source columns, check if immediate dependencies are the same as source columns
                immediate_deps_paths = set(dep["full_path"] for dep in immediate_deps_info)
                source_paths = set(src["full_path"] for src in source_info)
                
                if immediate_deps_paths == source_paths:
                    # If immediate dependencies are the same as source columns, only show source columns
                    column_info["column"]["source_columns"] = source_info
                else:
                    # Otherwise, include both immediate dependencies and source columns
                    column_info["column"]["immediate_dependencies"] = immediate_deps_info
                    column_info["column"]["source_columns"] = source_info
            
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
            "table_description": table.description,
            "groups": groups,
            "connections": sorted(connections, key=lambda x: (x["from"], x["to"])),
            "columns_lineage": columns_info  # Preserve original YAML order
        }
    
    def table_lineage_json_string(self, table_name: str) -> str:
        """Return complete table lineage JSON as formatted string."""
        return json.dumps(self.table_lineage_json(table_name), indent=2)
