"""
Objects package for DAG generator.

This package contains the core object classes for handling data lineage:
- Column: Represents database columns with lineage tracking
- Table: Represents database tables with column management
- Group: Represents database groups/schemas with table organization
"""

from .column import Column
from .table import Table
from .group import Group

__all__ = ['Column', 'Table', 'Group']
