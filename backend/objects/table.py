"""
Table class for handling table-level lineage in DAG generation.

This class represents a database table and tracks its dependencies and dependents
to build a complete lineage graph for data transformations.
"""

from typing import Set, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .column import Column


class Table:
    """
    Represents a database table with lineage tracking capabilities.
    
    Attributes:
        group (str): The group/schema this table belongs to (e.g., src, stg, mart)
        name (str): The table name
        columns (List[Column]): List of columns in this table
        description (str): Optional description of what this table represents
        dependencies (Set[Table]): Set of tables this table depends on
        dependents (Set[Table]): Set of tables that depend on this table
    """
    
    def __init__(self, group: str, name: str, columns: List['Column'] = None, description: str = ""):
        """
        Initialize a Table object.
        
        Args:
            group (str): The group/schema this table belongs to
            name (str): The table name
            columns (List[Column]): List of columns in this table (optional, can be added later)
            description (str): Optional description of what this table represents
        """
        self.group = group
        self.name = name
        self.columns = columns or []
        self.description = description
        self.dependencies: Set[Table] = set()
        self.dependents: Set[Table] = set()
        
        # Ensure all columns have a reference back to this table
        for column in self.columns:
            if column.table != self:
                column.table = self
    
    def link_table(self, table: 'Table') -> None:
        """
        Links two tables together. This table becomes a dependency of the other table,
        and the other table becomes a dependent of this table.
        
        This follows the YAML pattern where dependencies are defined backwards -
        the dependent table declares what it depends on.
        
        Args:
            table (Table): The table that depends on this table
        """
        self.dependents.add(table)
        table.dependencies.add(self)
    
    def get_previous_columns(self) -> Set['Column']:
        """
        Get all columns from tables that this table depends on.
        Returns the set of all columns that this table is built from.
        
        Returns:
            Set[Column]: Set of all columns from dependency tables
        """
        previous_columns = set()
        for table in self.dependencies:
            previous_columns.update(table.columns)
        return previous_columns
    
    def get_source_columns(self) -> Set['Column']:
        """
        Get all source columns that this table ultimately sources its data from.
        Recursively traverses the dependency chain to find all source columns.
        
        Returns:
            Set[Column]: Set of all source columns this table depends on
        """
        source_columns = set()
        visited_tables = set()  # To avoid infinite loops in case of circular dependencies
        
        def _collect_source_columns(table: 'Table'):
            if table in visited_tables:
                return
            visited_tables.add(table)
            
            if not table.dependencies:
                # This is a source table - add all its columns
                source_columns.update(table.columns)
            else:
                # Recursively get source columns from dependency tables
                for dep_table in table.dependencies:
                    _collect_source_columns(dep_table)
        
        _collect_source_columns(self)
        return source_columns
    
    def get_column_by_name(self, column_name: str) -> 'Column':
        """
        Get a column from this table by name.
        
        Args:
            column_name (str): The name of the column to find
            
        Returns:
            Column: The column with the specified name
            
        Raises:
            ValueError: If no column with the specified name is found
        """
        for column in self.columns:
            if column.name == column_name:
                return column
        raise ValueError(f"Column '{column_name}' not found in table '{self.get_full_name()}'")
    
    def get_full_name(self) -> str:
        """
        Get the fully qualified table name.
        
        Returns:
            str: Fully qualified name in format 'group.table'
        """
        return f"{self.group}.{self.name}"
    
    def __str__(self) -> str:
        """String representation of the table."""
        return self.get_full_name()
    
    def __eq__(self, other) -> bool:
        """Check equality based on full name."""
        if not isinstance(other, Table):
            return False
        return self.get_full_name() == other.get_full_name()
    
    def __hash__(self) -> int:
        """Hash based on full name for use in sets and dictionaries."""
        return hash(self.get_full_name())
    
    def get_all_connected_tables(self) -> Set['Table']:
        """
        Get all tables that are connected to this table through column-level lineage.
        This includes all tables that contain columns connected to any column in this table,
        both upstream and downstream in the lineage graph.
        
        Returns:
            Set[Table]: Set of all tables connected to this table through column lineage
        """
        connected_tables = set()
        
        # For each column in this table, get all its connected columns
        for column in self.columns:
            connected_columns = column.get_all_connected_columns()
            
            # Extract the unique tables from all connected columns
            for connected_column in connected_columns:
                # Now we can directly access the table object from the column
                connected_tables.add(connected_column.table)
        
        return connected_tables
    
    def get_lineage_tables(self) -> Set['Table']:
        """
        Get tables in the direct lineage of this table without creating cross-contamination.
        This prevents source tables from appearing connected to each other when they
        both feed into the same downstream table.
        
        Returns:
            Set[Table]: Set of tables in the direct lineage path of this table
        """
        lineage_tables = set()
        
        # For each column in this table, get its lineage columns (not all connected)
        for column in self.columns:
            lineage_columns = column.get_lineage_columns()
            
            # Extract the unique tables from all lineage columns
            for lineage_column in lineage_columns:
                lineage_tables.add(lineage_column.table)
        
        return lineage_tables
    
    def add_column(self, column: 'Column') -> None:
        """
        Add a column to this table.
        
        Args:
            column (Column): The column to add to this table
        """
        if column not in self.columns:
            self.columns.append(column)
            column.table = self
