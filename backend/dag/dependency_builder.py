"""
Dependency Builder for DAG Generator

This module handles building dependency relationships between objects:
1. Column-to-column dependencies based on YAML depends_on lists
2. Table-to-table dependencies derived from column relationships

This module works with objects created by the ObjectConstructor.
"""

from typing import Dict, List, Any
from collections import defaultdict

# Import our object classes
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from objects import Group, Table, Column


class DependencyBuilder:
    """
    Handles building dependency relationships between constructed objects.
    """
    
    def __init__(self, groups: Dict[str, 'Group'], tables: Dict[str, 'Table'], 
                 columns: Dict[str, 'Column'], yaml_data: List[Dict[str, Any]]):
        """
        Initialize the dependency builder with constructed objects.
        
        Args:
            groups: Dictionary of group objects
            tables: Dictionary of table objects  
            columns: Dictionary of column objects
            yaml_data: Loaded YAML data for dependency information
        """
        self.groups = groups
        self.tables = tables
        self.columns = columns
        self.yaml_data = yaml_data
    
    def build_column_dependencies(self) -> None:
        """
        Build all dependency relationships between columns.
        This must be done after all columns are created.
        """
        print("\n=== Building Column Dependencies ===")
        
        dependency_count = 0
        
        # First handle regular column dependencies from YAML
        for data in self.yaml_data:
            columns_data = data.get('columns', [])  # Handle missing columns field
            if not columns_data:
                continue
            
            # Use inferred group from folder structure, fallback to YAML group field
            group_name = data.get('_inferred_group', data.get('group'))
            table_name = data.get('table')
            
            if not group_name or not table_name:
                print(f"  ⚠ Skipping data: missing group or table")
                continue
            
            for column_data in columns_data:
                if 'name' not in column_data or 'depends_on' not in column_data:
                    continue
                
                column_name = column_data['name']
                column_key = f"{group_name}.{table_name}.{column_name}"
                
                if column_key not in self.columns:
                    print(f"  ⚠ Column {column_key} not found for dependency building")
                    continue
                
                target_column = self.columns[column_key]
                dependencies = column_data['depends_on']
                
                if not dependencies:  # Empty list means source column
                    continue
                
                for dep_key in dependencies:
                    if dep_key not in self.columns:
                        print(f"  ⚠ Dependency {dep_key} not found for {column_key}")
                        continue
                    
                    source_column = self.columns[dep_key]
                    
                    # Create the link: source -> target
                    source_column.add_link(target_column)
                    dependency_count += 1
                    
                    print(f"  ✓ {dep_key} -> {column_key}")
        
        # Then handle invisible columns for table-level dependencies
        dependency_count += self._build_invisible_column_dependencies()
        
        print(f"Built {dependency_count} column dependencies")
    
    def _build_invisible_column_dependencies(self) -> int:
        """
        Build dependencies for invisible columns that represent table-level dependencies.
        Each invisible column depends on ALL columns (including invisible) of the referenced table.
        This ensures correct table-level lineage without cross-contamination.
        
        Returns:
            int: Number of dependencies created
        """
        dependency_count = 0
        
        # Find invisible columns that have table dependencies
        for column_key, column in self.columns.items():
            if not column.is_invisible or not hasattr(column, '_table_depends_on'):
                continue
            
            for table_ref in column._table_depends_on:
                if table_ref not in self.tables:
                    print(f"  ⚠ Referenced table {table_ref} not found for invisible column {column_key}")
                    continue
                
                referenced_table = self.tables[table_ref]
                
                # Link invisible column to ALL columns of the referenced table
                # (both visible and invisible columns)
                for source_column in referenced_table.columns:
                    source_column.add_link(column)
                    dependency_count += 1
                    print(f"  ✓ {source_column.get_full_name()} -> {column_key} (table-level)")
        
        return dependency_count
    
    def build_table_dependencies(self) -> None:
        """
        Build table-level dependencies based on column dependencies.
        If any column in Table A depends on any column in Table B, then Table B -> Table A.
        """
        print("\n=== Building Table Dependencies ===")
        
        table_deps = defaultdict(set)
        
        # Analyze column dependencies to determine table dependencies
        for column_key, column in self.columns.items():
            if column.dependencies:
                target_table = column.table
                
                for dep_column in column.dependencies:
                    source_table = dep_column.table
                    
                    if source_table != target_table:  # Don't create self-dependencies
                        table_deps[target_table.get_full_name()].add(source_table.get_full_name())
        
        # Create table links
        dependency_count = 0
        for target_table_key, source_table_keys in table_deps.items():
            if target_table_key not in self.tables:
                continue
                
            target_table = self.tables[target_table_key]
            
            for source_table_key in source_table_keys:
                if source_table_key not in self.tables:
                    continue
                
                source_table = self.tables[source_table_key]
                source_table.link_table(target_table)
                dependency_count += 1
                
                print(f"  ✓ {source_table_key} -> {target_table_key}")
        
        print(f"Built {dependency_count} table dependencies")
    
    def build_all_dependencies(self) -> None:
        """
        Build all dependency relationships (columns and tables).
        """
        print(f"Building dependencies...")
        print("=" * 50)
        
        self.build_column_dependencies()
        self.build_table_dependencies()
        
        print("\n✅ Dependency building completed!")
