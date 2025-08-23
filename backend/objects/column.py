"""
Column class for handling column-level lineage in DAG generation.

This class represents a database column and tracks its dependencies and dependents
to build a complete lineage graph for data transformations.
"""

from typing import Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .table import Table


class Column:
    """
    Represents a database column with lineage tracking capabilities.
    
    Attributes:
        name (str): The column name
        table (Table): The table object this column belongs to
        description (str): Optional description of what this column represents
        dependencies (Set[Column]): Set of columns this column depends on
        dependents (Set[Column]): Set of columns that depend on this column
    """
    
    def __init__(self, name: str, table: 'Table', description: str = ""):
        """
        Initialize a Column object.
        
        Args:
            name (str): The column name
            table (Table): The table object this column belongs to
            description (str): Optional description of what this column represents
        """
        self.name = name
        self.table = table
        self.description = description
        self.dependencies: Set[Column] = set()
        self.dependents: Set[Column] = set()
    
    def add_link(self, column: 'Column') -> None:
        """
        Links two columns together. This column becomes a dependency of the other column,
        and the other column becomes a dependent of this column.
        
        Args:
            column (Column): The column that depends on this column
        """
        self.dependents.add(column)
        column.dependencies.add(self)
    
    def get_prev_columns(self) -> Set['Column']:
        """
        Get the set of columns that this column directly depends on.
        
        Returns:
            Set[Column]: Set of columns this column depends on
        """
        return self.dependencies.copy()
    
    def get_next_columns(self) -> Set['Column']:
        """
        Get the set of columns that directly depend on this column.
        
        Returns:
            Set[Column]: Set of columns that depend on this column
        """
        return self.dependents.copy()
    
    def get_source_columns(self) -> Set['Column']:
        """
        Get all source columns that this column ultimately depends on.
        If this column has no dependencies, returns itself.
        Otherwise, recursively gets source columns from all dependencies.
        
        Returns:
            Set[Column]: Set of all source columns this column depends on
        """
        if not self.dependencies:
            # This is a source column
            return {self}
        
        source_columns = set()
        visited = set()  # To avoid infinite loops in case of circular dependencies
        
        def _collect_sources(column: 'Column'):
            if column in visited:
                return
            visited.add(column)
            
            if not column.dependencies:
                # This is a source column
                source_columns.add(column)
            else:
                # Recursively get source columns from dependencies
                for dep in column.dependencies:
                    _collect_sources(dep)
        
        _collect_sources(self)
        return source_columns
    
    def get_full_name(self) -> str:
        """
        Get the fully qualified column name.
        
        Returns:
            str: Fully qualified name in format 'group.table.column'
        """
        return f"{self.table.group}.{self.table.name}.{self.name}"
    
    def __str__(self) -> str:
        """String representation of the column."""
        return self.get_full_name()
    
    def __eq__(self, other) -> bool:
        """Check equality based on full name."""
        if not isinstance(other, Column):
            return False
        return self.get_full_name() == other.get_full_name()
    
    def __hash__(self) -> int:
        """Hash based on full name for use in sets and dictionaries."""
        return hash(self.get_full_name())
    
    def get_all_connected_columns(self) -> Set['Column']:
        """
        Get all columns that this column is connected to, both forwards and backwards.
        This includes all dependencies (columns this column depends on) and all dependents
        (columns that depend on this column), traversed recursively.
        
        Returns:
            Set[Column]: Set of all columns connected to this column in the lineage graph
        """
        connected_columns = set()
        visited = set()  # To avoid infinite loops in case of circular dependencies
        
        def _collect_connected(column: 'Column'):
            if column in visited:
                return
            visited.add(column)
            connected_columns.add(column)
            
            # Traverse backwards (dependencies)
            for dep in column.dependencies:
                _collect_connected(dep)
            
            # Traverse forwards (dependents)
            for dependent in column.dependents:
                _collect_connected(dependent)
        
        _collect_connected(self)
        # Remove self from the result since we want connected columns, not including self
        connected_columns.discard(self)
        return connected_columns
