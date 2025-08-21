# main.py
from pathlib import Path
import sys
import networkx as nx
from loader import load_all_specs
from graph_builder import build_table_graph

def main() -> None:
    specs = load_all_specs(Path("tables"))
    g: nx.DiGraph = build_table_graph(specs)

    if len(sys.argv) == 2:
        table_id = sys.argv[1]  
        if table_id not in g.nodes:
            print(f"Table '{table_id}' not found. Use full 'group.table'.")
            sys.exit(1)

        upstream = nx.ancestors(g, table_id)
        downstream = nx.descendants(g, table_id)

        print(f"\nLineage for {table_id}:")
        print("\nUpstream (depends on):")
        for n in sorted(upstream):
            print("  ", n)

        print("\nDownstream (depended on by):")
        for n in sorted(downstream):
            print("  ", n)
        return

    print("Tables:")
    for n in g.nodes:
        print(" ", n)

    print("\nDependencies:")
    for src, dst in g.edges:
        print(f"  {src} -> {dst}")

if __name__ == "__main__":
    main()
