"""
Main DAG Assembler

This module orchestrates the complete DAG assembly process by coordinating
the ObjectConstructor and DependencyBuilder modules.
"""

from typing import Optional, Dict, Any
import json
from object_constructor import ObjectConstructor
from dependency_builder import DependencyBuilder

# Import our object classes
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from objects import Group, Table, Column


class DAGAssembler:
    """
    Main orchestrator for assembling the complete DAG structure.
    """
    
    def __init__(self):
        """Initialize the assembler."""
        self.constructor = ObjectConstructor()
        self.dependency_builder = None
        
    def assemble_from_project(self, project_path: str) -> None:
        """
        Complete assembly process: construct objects and build dependencies.
        
        Args:
            project_path: Path to the project directory containing YAML files
        """
        # Step 1: Construct all objects
        self.constructor.construct_objects(project_path)
        
        # Step 2: Build dependencies
        self.dependency_builder = DependencyBuilder(
            self.constructor.groups,
            self.constructor.tables, 
            self.constructor.columns,
            self.constructor.yaml_data
        )
        self.dependency_builder.build_all_dependencies()
        
        print("\n" + "=" * 50)
        print("✅ Complete DAG assembly finished!")
    
    @property
    def groups(self):
        """Access to constructed groups."""
        return self.constructor.groups
    
    @property  
    def tables(self):
        """Access to constructed tables."""
        return self.constructor.tables
    
    @property
    def columns(self):
        """Access to constructed columns."""
        return self.constructor.columns
    
    def get_group(self, group_name: str) -> Optional[Group]:
        """Get a group by name."""
        return self.constructor.groups.get(group_name)
    
    def get_table(self, group_name: str, table_name: str) -> Optional[Table]:
        """Get a table by group and table name."""
        return self.constructor.tables.get(f"{group_name}.{table_name}")
    
    def get_column(self, group_name: str, table_name: str, column_name: str) -> Optional[Column]:
        """Get a column by group, table, and column name."""
        return self.constructor.columns.get(f"{group_name}.{table_name}.{column_name}")

    def export_to_json(self, file_path: str) -> None:
        """
        Export the assembled DAG objects to a JSON file.
        
        Args:
            file_path: Path to the output JSON file
        """
        # Prepare data for JSON export
        data = {
            "groups": [
                {
                    "name": group_name,
                    "tables": [
                        {
                            "name": table.name,
                            "columns": [column.name for column in table.columns]
                        } for table in group.tables
                    ]
                } for group_name, group in self.constructor.groups.items()
            ]
        }
        
        # Write data to JSON file
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        
        print(f"✅ DAG objects exported to {file_path}")
    

def main():
    """Example usage of the DAG assembler."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dag_assembler.py <project_path>")
        print("Example: python dag_assembler.py Projects/finance")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    try:
        assembler = DAGAssembler()
        assembler.assemble_from_project(project_path)
        
        # Example: Access assembled objects
        print(f"\n=== Example Usage ===")
        
        # Show basic structure
        print(f"Groups: {len(assembler.groups)}")
        print(f"Tables: {len(assembler.tables)}")
        print(f"Columns: {len(assembler.columns)}")
        
        # Show groups and their tables
        for group_name, group in assembler.groups.items():
            print(f"\nGroup '{group_name}': {len(group.tables)} tables")
            for table in group.tables:
                print(f"  Table '{table.name}': {len(table.columns)} columns")
        
        # Export to JSON (for demonstration, exporting only the structure)
        assembler.export_to_json("dag_structure.json")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
