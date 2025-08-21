import networkx as nx
from models import TableSpec

def build_column_graph(specs: list[TableSpec]) -> nx.DiGraph:
    g = nx.DiGraph()
    for spec in specs:
        for col in spec.columns:
            tgt = f"{spec.group}.{spec.table}.{col.name}"
            g.add_node(tgt, group=spec.group, table=spec.table, column=col.name)
            for dep in col.depends_on:
                g.add_edge(dep, tgt)
    return g

def build_table_graph(specs: list[TableSpec]) -> nx.DiGraph:
    g = nx.DiGraph()
    for spec in specs:
        table_id = f"{spec.group}.{spec.table}"
        g.add_node(table_id, group=spec.group, table=spec.table)
        for col in spec.columns:
            for dep in col.depends_on:
                grp, tbl, _ = dep.split(".")
                g.add_edge(f"{grp}.{tbl}", table_id)
    return g
