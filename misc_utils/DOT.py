import pathlib
import pydot

root = pathlib.Path(
    r"C:\Users\RodePeters\Desktop\junk_drawer\test_flowapp_outbox\cartridge_flow_test_cal_RodePeters_20250428_172344"
)

# ── graph-wide style ───────────────────────────────────────────────
graph = pydot.Dot(
    graph_type="digraph",
    rankdir="TB",
    bgcolor="transparent",       # → transparent canvas
    color="white",               # edge color fallback
    fontcolor="white",           # global label color
    fontname="Helvetica",
)

# ── default node & edge appearance (white on transparent) ──────────
default_node = {'shape': 'box', 'style': 'filled', 'fillcolor': 'transparent',
                'color': 'white', 'fontcolor': 'white', 'fontname': 'Helvetica'}
default_edge = {'color': 'white'}

# ── walk the tree & populate graph ────────────────────────────────
for path in root.rglob("*"):
    child_name  = str(path.relative_to(root))
    parent_name = str(path.parent.relative_to(root)) if path != root else None

    # create / get child node
    graph.add_node(pydot.Node(child_name, **default_node))

    # create edge to parent
    if parent_name is not None:
        graph.add_node(pydot.Node(parent_name, **default_node))
        graph.add_edge(pydot.Edge(parent_name, child_name, **default_edge))

# ── write transparent PNG ──────────────────────────────────────────
graph.write_png("run_tree_white.png")
