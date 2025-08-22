# main.py
from __future__ import annotations
from pathlib import Path
import sys
import json
import networkx as nx
from loader import load_all_specs
from graph_builder import build_graph
from queries import lineage_subgraph
from json_export import graph_to_grouped_json

def print_tables_and_deps(g: nx.DiGraph) -> None:
    print("Tables:")
    for n in sorted(g.nodes):
        print(" ", n)

    print("\nDependencies:")
    for src, dst in sorted(g.edges):
        print(f"  {src} -> {dst}")

def main() -> None:
    specs = load_all_specs(Path("../Tables"))
    full_g: nx.DiGraph = build_graph(specs)

    # CLI:
    #   main.py                       -> print whole graph (text)
    #   main.py group.table           -> print lineage subgraph (text)
    #   main.py --json                -> print whole graph as MVP JSON
    #   main.py group.table --json    -> print lineage subgraph as MVP JSON
    args = sys.argv[1:]
    want_json = False
    table_id = None

    if args:
        if args[0] == "--json":
            want_json = True
        else:
            table_id = args[0]
            if len(args) > 1 and args[1] == "--json":
                want_json = True

    g: nx.DiGraph
    if table_id:
        try:
            g = lineage_subgraph(full_g, table_id)
        except KeyError as e:
            print(e)
            sys.exit(1)
    else:
        g = full_g

    if want_json:
        payload = graph_to_grouped_json(g)
        print(json.dumps(payload, indent=2))
    else:
        if table_id:
            print(f"\nLineage for {table_id}:")
        print_tables_and_deps(g)

if __name__ == "__main__":
    main()
