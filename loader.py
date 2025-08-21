from pathlib import Path
import yaml
from models import TableSpec

def load_table_spec(path: Path) -> TableSpec:
    with open(path) as f:
        data = yaml.safe_load(f)
    return TableSpec(**data)

def load_all_specs(root: Path) -> list[TableSpec]:
    return [load_table_spec(p) for p in root.rglob("*.y*ml")]
