import pathlib, pydot

root = pathlib.Path(
    r"C:\Users\RodePeters\Desktop\junk_drawer\test_flowapp_outbox\cartridge_flow_test_cal_RodePeters_20250423_101822"
)

graph = pydot.Dot(graph_type="digraph", rankdir="TB")

for path in root.rglob("*"):
    # turn Paths into plain strings (or use .as_posix() for forward-slashes)
    child_name  = str(path.relative_to(root))
    parent_name = str(path.parent.relative_to(root)) if path != root else None

    graph.add_node(pydot.Node(child_name))

    if parent_name is not None:
        graph.add_node(pydot.Node(parent_name))
        graph.add_edge(pydot.Edge(parent_name, child_name))

graph.write_png("run_tree.png")   # or .write_svg("run_tree.svg")
