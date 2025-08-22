import networkx as nx
from typing import Iterable
from models import TableSpec

def build_graph(specs: Iterable[TableSpec]) -> nx.DiGraph:
    """
    Build column-level lineage internally, then collapse to a table-only DiGraph.

    Returns:
        nx.DiGraph with nodes as "group.table" (attrs: group, table),
        edges inferred from any column->column dependency between those tables.
    """
    # 1) Build column graph (internal)
    col_g = nx.DiGraph()
    for spec in specs:
        tgt_table_id = f"{spec.group}.{spec.table}"
        for col in spec.columns:
            tgt_col_id = f"{tgt_table_id}.{col.name}"
            # track rich attrs at column level (internal only)
            col_g.add_node(
                tgt_col_id,
                group=spec.group,
                table=spec.table,
                column=col.name,
            )
            for dep in col.depends_on or []:
                # dep is expected like "group.table.column"
                col_g.add_edge(dep, tgt_col_id)

    # 2) Collapse column graph -> table graph
    tbl_g = nx.DiGraph()

    # helper: derive table id from any node id
    def table_id(node_id: str) -> str:
        # robust split: take first two segments as group.table, ignore the rest
        parts = node_id.split(".", 2)  # max 3 parts
        if len(parts) < 2:
            # fallback: treat entire thing as table name with empty group
            return f".{node_id}"
        return f"{parts[0]}.{parts[1]}"

    # add table nodes from all columns we saw
    for node_id, a in col_g.nodes(data=True):
        tid = table_id(node_id)
        # preserve group/table attrs
        group = a.get("group") or tid.split(".", 1)[0]
        table = a.get("table") or tid.split(".", 1)[1] if "." in tid else tid
        if tid not in tbl_g:
            tbl_g.add_node(tid, group=group, table=table)

    # also ensure we add nodes for any tables referenced only as sources (deps with no target columns)
    for u, v in col_g.edges():
        for nid in (u, v):
            tid = table_id(nid)
            if tid not in tbl_g:
                # if we never saw attrs, best-effort split
                grp, tbl = (tid.split(".", 1) + [""])[:2] if "." in tid else ("", tid)
                tbl_g.add_node(tid, group=grp, table=tbl)

    # add table->table edges derived from any column->column edge
    for u, v in col_g.edges():
        src_tbl = table_id(u)
        dst_tbl = table_id(v)
        if src_tbl != dst_tbl:
            tbl_g.add_edge(src_tbl, dst_tbl)

    # 3) Ensure isolated tables (with columns but no deps) are present (already added above)
    # No extra work needed; nodes exist even if degree 0.

    return tbl_g
