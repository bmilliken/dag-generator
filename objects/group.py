"""
Group class for handling group-level organization in DAG generation.

This class represents a database group/schema and contains multiple tables
to organize the data transformation pipeline.
"""

from typing import List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .table import Table
    from .column import Column


class Group:
    """
    Represents a database group/schema with multiple tables.
    
    Attributes:
        name (str): The name of the group (e.g., src, stg, mart)
        tables (List[Table]): List of tables in this group
        description (str): Optional description of what this group represents
    """
    
    def __init__(self, name: str, tables: List['Table'] = None, description: str = ""):
        """
        Initialize a Group object.
        
        Args:
            name (str): The name of the group
            tables (List[Table]): List of tables in this group (optional, can be added later)
            description (str): Optional description of what this group represents
        """
        self.name = name
        self.tables = tables or []
        self.description = description
    
    def add_table(self, table: 'Table') -> None:
        """
        Add a table to this group.
        
        Args:
            table (Table): The table to add to this group
        """
        if table not in self.tables:
            self.tables.append(table)
    
    def get_table_by_name(self, table_name: str) -> 'Table':
        """
        Get a table from this group by name.
        
        Args:
            table_name (str): The name of the table to find
            
        Returns:
            Table: The table with the specified name
            
        Raises:
            ValueError: If no table with the specified name is found
        """
        for table in self.tables:
            if table.name == table_name:
                return table
        raise ValueError(f"Table '{table_name}' not found in group '{self.name}'")
    
    def get_all_columns(self) -> Set['Column']:
        """
        Get all columns from all tables in this group.
        
        Returns:
            Set[Column]: Set of all columns in this group
        """
        all_columns = set()
        for table in self.tables:
            all_columns.update(table.columns)
        return all_columns
    
    def get_dependencies(self) -> Set['Group']:
        """
        Get all groups that this group depends on (through table dependencies).
        
        Returns:
            Set[Group]: Set of groups this group depends on
        """
        dependent_groups = set()
        for table in self.tables:
            for dep_table in table.dependencies:
                # Assuming the table's group attribute points to the group name
                # In a full implementation, you'd want a back-reference to the Group object
                if hasattr(dep_table, 'group_obj') and dep_table.group_obj != self:
                    dependent_groups.add(dep_table.group_obj)
        return dependent_groups
    
    def __str__(self) -> str:
        """String representation of the group."""
        return self.name
    
    def __repr__(self) -> str:
        """Detailed string representation of the group."""
        return f"Group(name='{self.name}', tables={len(self.tables)})"
    
    def __eq__(self, other) -> bool:
        """Check equality based on name."""
        if not isinstance(other, Group):
            return False
        return self.name == other.name
    
    def __hash__(self) -> int:
        """Hash based on name for use in sets and dictionaries."""
        return hash(self.name)
