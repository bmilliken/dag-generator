from typing import List
from pydantic import BaseModel, Field, validator

class ColumnSpec(BaseModel):
    name: str
    depends_on: List[str] = Field(default_factory=list)
    @validator("depends_on", each_item=True)
    def validate_dep(cls, v: str) -> str:
        if v.count(".") != 2:
            raise ValueError(f"Dependency must be group.table.column, got: {v}")
        return v

class TableSpec(BaseModel):
    group: str
    table: str
    columns: List[ColumnSpec]
