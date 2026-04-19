import graphviz

# ──────────────────────────────────────────────────────────────────────────────
# Color Themes
# ──────────────────────────────────────────────────────────────────────────────

THEMES = {
    "Clàssic": {
        "male":        "#dce6f1",
        "female":      "#f8e8f0",
        "unknown":     "#e8e8e8",
        "sep_bg":      "#f0ece4",
        "sep_color":   "#8b6d1e",
        "font_main":   "#1a2332",
        "border":      "#b0b8c8",
        "root_border": "#c8900a",
        "edge":        "#778899",
    },
    "Terra": {
        "male":        "#d4c5a9",
        "female":      "#c9b0bd",
        "unknown":     "#d6cfc4",
        "sep_bg":      "#e8dcc8",
        "sep_color":   "#6b4c1e",
        "font_main":   "#3e2f1c",
        "border":      "#a08060",
        "root_border": "#b8860b",
        "edge":        "#8b7355",
    },
    "Oceà": {
        "male":        "#b8d4e8",
        "female":      "#d4b8e8",
        "unknown":     "#c0d4e0",
        "sep_bg":      "#ddeef8",
        "sep_color":   "#1e5a7a",
        "font_main":   "#0d2b40",
        "border":      "#5b8ca8",
        "root_border": "#e07820",
        "edge":        "#4a7a9b",
    },
    "Bosc": {
        "male":        "#c8ddc8",
        "female":      "#ddc8d8",
        "unknown":     "#d0d8c8",
        "sep_bg":      "#e8f0e0",
        "sep_color":   "#3a6a2a",
        "font_main":   "#1a3020",
        "border":      "#5a8060",
        "root_border": "#c8700a",
        "edge":        "#6a9060",
    },
}

BW_THEME = {
    "male":        "#f4f4f4",
    "female":      "#ebebeb",
    "unknown":     "#e8e8e8",
    "sep_bg":      "#dddddd",
    "sep_color":   "#444444",
    "font_main":   "#111111",
    "border":      "#555555",
    "root_border": "#000000",
    "edge":        "#555555",
}

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _escape(text):
    """Escape XML/HTML special characters for Graphviz HTML labels."""
    if not text:
        return text
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _gender_bg(gender, theme, use_gender_colors):
    if not use_gender_colors:
        return theme["unknown"]
    if gender == "M":
        return theme["male"]
    if gender == "F":
        return theme["female"]
    return theme["unknown"]


def _person_rows(details, bg, theme, show_birth, show_death, show_location, is_spouse=False, node_width=None, compact_mode=False, prefix=None):
    """
    Build Graphviz HTML <TR> rows for one person's info block.
    Returns a list of HTML strings.
    """
    rows = []
    fc = _escape(theme["font_main"])
    
    if compact_mode:
        pad_name = "2" if is_spouse else "2"
    else:
        pad_name = "3" if is_spouse else "4"
        
    size_name = "10"
    size_date = "8"
    wa = f' WIDTH="{node_width}"' if node_width else ""

    if not details:
        label_text = f"<I>{prefix or ''}Desconegut/da</I>"
        rows.append(
            f'<TR><TD ALIGN="CENTER" BGCOLOR="{bg}" CELLPADDING="{pad_name}"{wa}>'
            f'<FONT FACE="Segoe UI, Arial" POINT-SIZE="{size_name}" COLOR="{fc}">{label_text}</FONT>'
            f'</TD></TR>'
        )
        return rows

    name = _escape(details.get("name", "?"))
    inner_label = f"<B>{name}</B>"
    if is_spouse:
        inner_label = f"<I>{inner_label}</I>"
    
    if prefix:
         # Use separator color for the symbol even when inline
         sep_color = _escape(theme["sep_color"])
         inner_label = f'<FONT COLOR="{sep_color}">{prefix}</FONT>{inner_label}'
        
    rows.append(
        f'<TR><TD ALIGN="CENTER" BGCOLOR="{bg}" CELLPADDING="{pad_name}"{wa}>'
        f'<FONT FACE="Segoe UI, Arial" POINT-SIZE="{size_name}" COLOR="{fc}">{inner_label}</FONT>'
        f'</TD></TR>'
    )

    # Build date line (birth + death on one compact line)
    parts = []
    if show_birth and details.get("birth_date"):
        loc = (f" {_escape(details['birth_place'])}"
               if show_location and details.get("birth_place") else "")
        parts.append(f"b. {_escape(details['birth_date'])}{loc}")
    if show_death and details.get("death_date"):
        loc = (f" {_escape(details['death_place'])}"
               if show_location and details.get("death_place") else "")
        parts.append(f"d. {_escape(details['death_date'])}{loc}")

    if parts:
        rows.append(
            f'<TR><TD ALIGN="CENTER" BGCOLOR="{bg}" CELLPADDING="1"{wa}>'
            f'<FONT FACE="Segoe UI, Arial" POINT-SIZE="{size_date}" COLOR="{fc}">{"   ".join(parts)}</FONT>'
            f'</TD></TR>'
        )

    return rows


def _separator_row(theme, marriage_num=None, node_width=None):
    """⚭ separator row between main person and spouse."""
    sep_bg = theme["sep_bg"]
    sep_color = theme["sep_color"]
    label = f"&#x26AD; ({marriage_num})" if marriage_num else "&#x26AD;"
    wa = f' WIDTH="{node_width}"' if node_width else ""
    return (
        f'<TR><TD ALIGN="CENTER" BGCOLOR="{sep_bg}" CELLPADDING="1"{wa}>'
        f'<FONT FACE="Segoe UI, Arial" POINT-SIZE="9" COLOR="{sep_color}"><I>{label}</I></FONT>'
        f'</TD></TR>'
    )

# ──────────────────────────────────────────────────────────────────────────────
# Label builders
# ──────────────────────────────────────────────────────────────────────────────

def _build_indi_label(node, show_birth, show_death, show_location, theme, use_gender_colors, rounded_corners=True, node_width=None, is_root=False, compact_mode=False):
    """
    HTML label for an INDI node.
    """
    main   = node["main"]
    spouses = node.get("spouses", [])
    has_multi = node.get("has_multiple_marriages", False)

    rows = []

    # Main person
    main_bg = _gender_bg(main.get("gender", "U"), theme, use_gender_colors)
    rows += _person_rows(main, main_bg, theme, show_birth, show_death, show_location, is_spouse=False, node_width=node_width, compact_mode=compact_mode)

    for sp_info in spouses:
        m_num = sp_info["marriage_num"] if has_multi else None
        sp_details = sp_info.get("details")
        sp_gender = sp_details.get("gender", "U") if sp_details else "U"
        sp_bg = _gender_bg(sp_gender, theme, use_gender_colors)
        
        prefix = None
        if compact_mode:
            prefix = f"&#x26AD; ({m_num}) " if m_num else "&#x26AD; "
        else:
            rows.append(_separator_row(theme, m_num, node_width=node_width))
            
        rows += _person_rows(sp_details, sp_bg, theme, show_birth, show_death, show_location, 
                             is_spouse=True, node_width=node_width, compact_mode=compact_mode, prefix=prefix)

    style = ' STYLE="ROUNDED"' if rounded_corners else ""
    border_w = "3" if is_root else "1"
    border_c = theme["root_border"] if is_root else theme["border"]
    
    return f'<<TABLE BORDER="{border_w}" COLOR="{border_c}" CELLBORDER="0" CELLSPACING="0"{style}>{"".join(rows)}</TABLE>>'


def _build_fam_label(node, show_birth, show_death, show_location, theme, use_gender_colors, rounded_corners=True, node_width=None, is_root=False, compact_mode=False):
    """
    HTML label for a FAM (ancestor couple) node.
    """
    husband = node.get("husband")
    wife    = node.get("wife")

    rows = []

    h_bg = _gender_bg("M", theme, use_gender_colors)
    rows += _person_rows(husband, h_bg, theme, show_birth, show_death, show_location, is_spouse=False, node_width=node_width, compact_mode=compact_mode)

    if wife:
        prefix = None
        if compact_mode:
            prefix = "&#x26AD; "
        elif husband:
            rows.append(_separator_row(theme, node_width=node_width))
            
        w_bg = _gender_bg("F", theme, use_gender_colors)
        rows += _person_rows(wife, w_bg, theme, show_birth, show_death, show_location, is_spouse=True, node_width=node_width, compact_mode=compact_mode, prefix=prefix)

    style = ' STYLE="ROUNDED"' if rounded_corners else ""
    border_w = "3" if is_root else "1"
    border_c = theme["root_border"] if is_root else theme["border"]
    
    return f'<<TABLE BORDER="{border_w}" COLOR="{border_c}" CELLBORDER="0" CELLSPACING="0"{style}>{"".join(rows)}</TABLE>>'


# ──────────────────────────────────────────────────────────────────────────────
# Generation depth (BFS from root)
# ──────────────────────────────────────────────────────────────────────────────

def _calculate_generations(nodes, edges, root_id):
    """
    BFS to compute generation depth of each node.
    edges: list of {"from_id", "to_id"} dicts
    """
    if not root_id:
        # Default fallback if no root (e.g. debugging)
        return {n["id"]: 0 for n in nodes}

    children_of = {}
    parents_of  = {}
    for e in edges:
        p, c = e["from_id"], e["to_id"]
        children_of.setdefault(p, []).append(c)
        parents_of.setdefault(c, []).append(p)

    generations = {root_id: 0}
    queue = [root_id]
    while queue:
        cur = queue.pop(0)
        g = generations[cur]
        # For ancestors/descendants we want a consistent depth grid
        for nb in children_of.get(cur, []) + parents_of.get(cur, []):
            if nb not in generations:
                generations[nb] = g + 1
                queue.append(nb)

    # Ensure all nodes have some value
    for n in nodes:
        if n["id"] not in generations:
            generations[n["id"]] = 0

    return generations


# ──────────────────────────────────────────────────────────────────────────────
# Main graph generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_graph(nodes, edges, layout="Vertical", show_birth=True, show_death=True,
                   show_location=True, theme_name="Clàssic", use_gender_colors=True,
                   root_id=None, rounded_corners=True, node_width=None, compact_mode=False):
    """Generates a beautifully styled graphviz Digraph from the node/edge data."""

    rankdir = "TB" if layout == "Vertical" else "LR"
    engine  = "dot"

    theme = THEMES.get(theme_name, THEMES["Clàssic"]) if use_gender_colors else BW_THEME

    dot = graphviz.Digraph(engine=engine)
    dot.attr(rankdir=rankdir)
    dot.attr(size="8.3,11.7")
    dot.attr(ratio="compress")
    dot.attr(dpi="300")
    dot.attr(bgcolor="white")
    dot.attr(pad="0.5")
    
    if compact_mode:
        dot.attr(nodesep="0.15")
        dot.attr(ranksep="0.4")
    else:
        dot.attr(nodesep="0.5")
        dot.attr(ranksep="1.2")
    
    # Improved tree-like layout for orthogonal routing
    dot.attr(ranker="longest-path") 
    dot.attr(splines="ortho")

    # Default: borderless nodes (HTML table provides borders)
    # Shape "none" is crucial for HTML labels
    dot.attr("node",
             shape="none",
             margin="0",
             penwidth="0")

    dot.attr("edge",
             color=theme["edge"],
             arrowsize="0.5",
             penwidth="0.9",
             arrowhead="none",
             fontsize="8",
             fontname="Segoe UI, Arial",
             fontcolor="#999999")

    # Calculate generations for rank=same grouping
    generations = _calculate_generations(nodes, edges, root_id)
    nodes_by_gen = {}
    for node in nodes:
        gen = generations.get(node["id"], 0)
        nodes_by_gen.setdefault(gen, []).append(node)

    # Add nodes grouped by generation in subgraphs to force alignment (rank=same)
    for gen, gen_nodes in nodes_by_gen.items():
        with dot.subgraph() as s:
            s.attr(rank="same")
            for node in gen_nodes:
                nid = node["id"]
                is_r = (nid == root_id)
                if node["type"] == "indi":
                    label = _build_indi_label(node, show_birth, show_death, show_location,
                                              theme, use_gender_colors,
                                              rounded_corners=rounded_corners,
                                              node_width=node_width,
                                              is_root=is_r,
                                              compact_mode=compact_mode)
                else:
                    label = _build_fam_label(node, show_birth, show_death, show_location,
                                             theme, use_gender_colors,
                                             rounded_corners=rounded_corners,
                                             node_width=node_width,
                                             is_root=is_r,
                                             compact_mode=compact_mode)

                attrs = {"label": label}
                s.node(nid, **attrs)

    # Group ALL edges by from_id to create ONE clean fork per parent node
    edge_groups = {}
    for edge in edges:
        from_id = edge["from_id"]
        edge_groups.setdefault(from_id, []).append(edge)

    junctions_by_gen = {}
    
    for from_id, group in edge_groups.items():
        t_port = "s"
        h_port = "n"
        if layout == "Horizontal":
            t_port = "e"
            h_port = "w"
            
        # Create a unique main junction ID for the parent's single trunk
        j_main = f"junc_{from_id}".replace('@', '')
        dot.node(j_main, shape="point", width="0", height="0", margin="0")
        
        # Weight 9999 on the parent trunk forces the main junction to strictly share the Y-coordinate 
        p_attrs = {"dir": "none", "weight": "9999"} 
        dot.edge(f"{from_id}:{t_port}", j_main, **p_attrs)
        
        gen = generations.get(from_id, 0)
        junctions_by_gen.setdefault(gen, []).append(j_main)

        # To force PERFECT ortho 90-degree elbows, create a discrete junction for EACH child
        # and connect them vertically as a rigid bus. 
        j_children = []
        for i, e in enumerate(group):
            j_c = f"junc_{from_id}_c{i}".replace('@', '')
            dot.node(j_c, shape="point", width="0", height="0", margin="0")
            j_children.append(j_c)
            junctions_by_gen.setdefault(gen, []).append(j_c)
            
            # Connect the individual junction horizontally to the child WITHOUT compass port
            # Graphviz ignores weight if compass ports are specified. We need weight=9999 to pull it exactly to Child's Y!
            e_attrs = {"weight": "9999"} 
            if e.get("label"):
                e_attrs["xlabel"] = e["label"]
            dot.edge(j_c, f'{e["to_id"]}', **e_attrs)

        # Connect the children junctions together to form the rigid vertical bus
        # Weight 0 and constraint=false so it doesn't pull them vertically!
        for i in range(len(j_children) - 1):
            dot.edge(j_children[i], j_children[i+1], dir="none", weight="0", constraint="false")
            
        # Tie the main parent junction into the rigid bus without forcing topology distortion
        if j_children:
            dot.edge(j_main, j_children[0], dir="none", weight="0", constraint="false")

    # Force all junctions of the same generation into a dedicated intermediate rank
    # This prevents the vertical trunk routing from intersecting with wider node boxes
    for gen, j_nodes in junctions_by_gen.items():
        if len(j_nodes) > 0:
            with dot.subgraph() as s:
                s.attr(rank="same")
                for j in j_nodes:
                    s.node(j)

    return dot

# ──────────────────────────────────────────────────────────────────────────────
# Export helpers
# ──────────────────────────────────────────────────────────────────────────────

def render_to_svg(dot):
    """Returns raw SVG string."""
    try:
        return dot.pipe(format="svg").decode("utf-8")
    except graphviz.ExecutableNotFound:
        return "<text>Error: Graphviz executable not found. Please install Graphviz.</text>"


def render_to_pdf(dot, output_path):
    """Saves to PDF."""
    try:
        dot.render(output_path, format="pdf", cleanup=True)
        return True
    except graphviz.ExecutableNotFound:
        return False
