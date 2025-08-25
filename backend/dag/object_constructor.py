"""
Object Constructor for DAG Generator

This module handles parsing YAML files and constructing the basic object hierarchy:
1. Groups (collections of tables)
2. Tables (collections of columns) 
3. Columns (basic structure without dependencies)

Dependencies are handled separately by the dependency_builder module.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any

# Import our object classes
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from objects import Group, Table, Column


class ObjectConstructor:
    """
    Handles construction of Groups, Tables, and Columns from YAML files.
    """
    
    def __init__(self):
        """Initialize the constructor with empty collections."""
        self.groups: Dict[str, Group] = {}
        self.tables: Dict[str, Table] = {}  # Key format: "group.table"
        self.columns: Dict[str, Column] = {}  # Key format: "group.table.column"
        self.yaml_data: List[Dict[str, Any]] = []
        
    def load_yaml_files(self, project_path: str) -> None:
        """
        Load all YAML files from a project directory.
        
        Args:
            project_path: Path to the project directory containing YAML files
        """
        project_dir = Path(project_path)
        
        if not project_dir.exists():
            raise FileNotFoundError(f"Project directory '{project_path}' does not exist")
        
        yaml_files = list(project_dir.glob("*.yml")) + list(project_dir.glob("*.yaml"))
        
        if not yaml_files:
            raise ValueError(f"No YAML files found in '{project_path}'")
        
        print(f"Loading {len(yaml_files)} YAML files from {project_path}")
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)
                    if data:  # Skip empty files
                        data['_source_file'] = str(yaml_file)
                        self.yaml_data.append(data)
                        print(f"  ✓ Loaded {yaml_file.name}")
            except Exception as e:
                print(f"  ✗ Error loading {yaml_file.name}: {e}")
                raise
    
    def create_groups(self) -> None:
        """
        Create all Group objects from the YAML data.
        Groups are identified by unique group names across all YAML files.
        """
        print("\n=== Creating Groups ===")
        
        group_names = set()
        for data in self.yaml_data:
            if 'group' in data:
                group_names.add(data['group'])
        
        for group_name in sorted(group_names):
            group = Group(group_name, [])
            self.groups[group_name] = group
            print(f"  ✓ Created group: {group_name}")
        
        print(f"Created {len(self.groups)} groups")
    
    def create_tables(self) -> None:
        """
        Create all Table objects and assign them to their respective groups.
        """
        print("\n=== Creating Tables ===")
        
        for data in self.yaml_data:
            if 'group' not in data or 'table' not in data:
                print(f"  ⚠ Skipping invalid data: missing group or table")
                continue
            
            group_name = data['group']
            table_name = data['table']
            table_key = f"{group_name}.{table_name}"
            
            # Get table description if available
            description = data.get('description', f"Table {table_name} in {group_name} group")
            
            # Create table with empty columns list (will be populated later)
            table = Table(group_name, table_name, [], description)
            
            # Add to our collections
            self.tables[table_key] = table
            
            # Add to the appropriate group
            if group_name in self.groups:
                self.groups[group_name].add_table(table)
            
            print(f"  ✓ Created table: {table_key}")
        
        print(f"Created {len(self.tables)} tables")
    
    def create_columns(self) -> None:
        """
        Create all Column objects and assign them to their respective tables.
        Also handles table-level dependencies by creating invisible columns.
        """
        print("\n=== Creating Columns ===")
        
        for data in self.yaml_data:
            group_name = data['group']
            table_name = data['table']
            table_key = f"{group_name}.{table_name}"
            
            if table_key not in self.tables:
                print(f"  ⚠ Table {table_key} not found, skipping columns")
                continue
            
            table = self.tables[table_key]
            
            # First, handle table-level dependencies if they exist
            table_depends_on = data.get('table_depends_on', [])
            if table_depends_on:
                print(f"  ℹ Processing table-level dependencies for {table_key}: {table_depends_on}")
                self._create_invisible_columns_for_table_dependencies(table, table_depends_on)
            
            # Then handle regular column definitions (if present)
            columns_data = data.get('columns', [])
            for column_data in columns_data:
                if 'name' not in column_data:
                    print(f"  ⚠ Column missing name in {table_key}")
                    continue
                
                column_name = column_data['name']
                column_key = f"{group_name}.{table_name}.{column_name}"
                description = column_data.get('description', f"Column {column_name}")
                key_type = column_data.get('key_type', "")
                
                # Create column with reference to table (visible column)
                column = Column(column_name, table, description, key_type, is_invisible=False)
                
                # Add to our collections
                self.columns[column_key] = column
                table.add_column(column)
                
                print(f"  ✓ Created column: {column_key}")
        
        print(f"Created {len(self.columns)} columns")
    
    def _create_invisible_columns_for_table_dependencies(self, table: Table, table_depends_on: List[str]) -> None:
        """
        Create invisible columns for table-level dependencies.
        Each invisible column depends on all columns from the referenced table.
        
        Args:
            table: The table that has table-level dependencies
            table_depends_on: List of table references (e.g., ['src.customers'])
        """
        for table_ref in table_depends_on:
            if table_ref not in self.tables:
                print(f"    ⚠ Referenced table {table_ref} not found for table-level dependency")
                continue
            
            referenced_table = self.tables[table_ref]
            
            # Create an invisible column that represents the table-level dependency
            invisible_column_name = f"__table_dep_{table_ref.replace('.', '_')}"
            invisible_column_key = f"{table.get_full_name()}.{invisible_column_name}"
            
            # Create the invisible column
            invisible_column = Column(
                name=invisible_column_name,
                table=table,
                description=f"Invisible column for table-level dependency on {table_ref}",
                key_type="",
                is_invisible=True
            )
            
            # Add to collections
            self.columns[invisible_column_key] = invisible_column
            table.add_column(invisible_column)
            
            print(f"    ✓ Created invisible column: {invisible_column_key}")
            
            # Note: Dependencies will be linked later by dependency_builder
            # We store the table reference for later linking
            if not hasattr(invisible_column, '_table_depends_on'):
                invisible_column._table_depends_on = []
            invisible_column._table_depends_on.append(table_ref)
    
    def construct_objects(self, project_path: str) -> None:
        """
        Complete object construction process.
        
        Args:
            project_path: Path to the project directory containing YAML files
        """
        print(f"Constructing objects from project: {project_path}")
        print("=" * 50)
        
        # Load YAML files and create object hierarchy
        self.load_yaml_files(project_path)
        self.create_groups()
        self.create_tables()
        self.create_columns()
        
        print("\n✅ Object construction completed!")
    
