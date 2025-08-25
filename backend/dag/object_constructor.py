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
        
    def _parse_multi_table_yaml(self, content: str, source_file: str, group_name: str) -> List[Dict[str, Any]]:
        """
        Parse a YAML file that may contain multiple table definitions.
        Each 'table:' keyword starts a new table definition.
        
        Args:
            content: Raw YAML file content
            source_file: Path to the source file
            group_name: Inferred group name from folder structure
            
        Returns:
            List of table data dictionaries
        """
        # Try to parse as a single YAML document first
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            print(f"  ✗ YAML parse error in {source_file}: {e}")
            return []
        
        if not data:
            return []
        
        # Check if this is a multi-table format by looking for multiple 'table' keys
        # Split content by lines and look for lines that start with 'table:'
        lines = content.strip().split('\n')
        table_start_lines = []
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith('table:') and not stripped_line.startswith('table_depends_on:'):
                table_start_lines.append(i)
        
        if len(table_start_lines) <= 1:
            # Single table format - handle as before
            if isinstance(data, dict) and 'table' in data:
                data['_source_file'] = source_file
                data['_inferred_group'] = group_name
                return [data]
            elif isinstance(data, dict) and 'tables' in data:
                # Legacy multi-table format with 'tables:' key
                table_entries = []
                for table_data in data['tables']:
                    table_entry = {
                        '_source_file': source_file,
                        '_inferred_group': group_name,
                        'table': table_data['table'],
                        'description': table_data.get('description', ''),
                        'columns': table_data.get('columns', []),
                        'table_depends_on': table_data.get('table_depends_on', [])
                    }
                    table_entries.append(table_entry)
                return table_entries
            else:
                return []
        
        # Multiple table format - split content by 'table:' occurrences
        table_entries = []
        for i, start_line in enumerate(table_start_lines):
            # Determine end of this table definition
            if i + 1 < len(table_start_lines):
                end_line = table_start_lines[i + 1]
                table_content_lines = lines[start_line:end_line]
            else:
                table_content_lines = lines[start_line:]
            
            # Join lines and parse as YAML
            table_content = '\n'.join(table_content_lines)
            
            try:
                table_data = yaml.safe_load(table_content)
                if table_data and isinstance(table_data, dict) and 'table' in table_data:
                    table_data['_source_file'] = source_file
                    table_data['_inferred_group'] = group_name
                    table_entries.append(table_data)
            except yaml.YAMLError as e:
                print(f"  ✗ Error parsing table definition starting at line {start_line + 1} in {source_file}: {e}")
                continue
        
        return table_entries
    
    def load_yaml_files(self, project_path: str) -> None:
        """
        Load all YAML files from a project directory and subdirectories.
        Groups are determined by subfolder names, not YAML content.
        
        Args:
            project_path: Path to the project directory containing YAML files and group subdirectories
        """
        project_dir = Path(project_path)
        
        if not project_dir.exists():
            raise FileNotFoundError(f"Project directory '{project_path}' does not exist")
        
        # Find all YAML files in project directory and subdirectories
        yaml_files = list(project_dir.rglob("*.yml")) + list(project_dir.rglob("*.yaml"))
        
        if not yaml_files:
            raise ValueError(f"No YAML files found in '{project_path}' or its subdirectories")
        
        print(f"Loading {len(yaml_files)} YAML files from {project_path}")
        
        for yaml_file in yaml_files:
            try:
                # Determine group from folder structure
                relative_path = yaml_file.relative_to(project_dir)
                if len(relative_path.parts) > 1:
                    # File is in a subdirectory - use subdirectory name as group
                    group_name = relative_path.parts[0]
                else:
                    # File is in root directory - use 'default' as group or extract from filename
                    group_name = 'default'
                
                with open(yaml_file, 'r') as f:
                    content = f.read()
                    
                    # Parse multiple table definitions in a single file
                    table_entries = self._parse_multi_table_yaml(content, str(yaml_file), group_name)
                    self.yaml_data.extend(table_entries)
                        
                print(f"  ✓ Loaded {yaml_file.name} (group: {group_name})")
            except Exception as e:
                print(f"  ✗ Error loading {yaml_file.name}: {e}")
                raise
    
    def create_groups(self) -> None:
        """
        Create all Group objects from the inferred group names.
        Groups are determined by subfolder structure, not YAML content.
        """
        print("\n=== Creating Groups ===")
        
        group_names = set()
        for data in self.yaml_data:
            if '_inferred_group' in data:
                group_names.add(data['_inferred_group'])
            elif 'group' in data:
                # Fallback to YAML group field for backward compatibility
                group_names.add(data['group'])
        
        for group_name in sorted(group_names):
            group = Group(group_name, [])
            self.groups[group_name] = group
            print(f"  ✓ Created group: {group_name}")
        
        print(f"Created {len(self.groups)} groups")
    
    def create_tables(self) -> None:
        """
        Create all Table objects and assign them to their respective groups.
        Groups are determined by folder structure.
        """
        print("\n=== Creating Tables ===")
        
        for data in self.yaml_data:
            if 'table' not in data:
                print(f"  ⚠ Skipping invalid data: missing table name")
                continue
            
            # Use inferred group from folder structure, fallback to YAML group field
            group_name = data.get('_inferred_group', data.get('group'))
            if not group_name:
                print(f"  ⚠ Skipping table: no group found")
                continue
                
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
        Groups are determined by folder structure.
        """
        print("\n=== Creating Columns ===")
        
        for data in self.yaml_data:
            # Use inferred group from folder structure, fallback to YAML group field
            group_name = data.get('_inferred_group', data.get('group'))
            table_name = data.get('table')
            
            if not group_name or not table_name:
                print(f"  ⚠ Skipping invalid data: missing group or table")
                continue
                
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

