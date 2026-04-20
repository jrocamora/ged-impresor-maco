from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
import os

def _ensure_utf8_sig(file_path):
    """
    Attempts to read the file with various encodings and rewrites it as utf-8-sig
    to ensure compatibility with the python-gedcom library.
    """
    encodings = ['utf-8-sig', 'utf-8', 'iso-8859-1', 'cp1252', 'utf-16']
    
    with open(file_path, 'rb') as f:
        content = f.read()
    
    decoded_content = None
    for enc in encodings:
        try:
            decoded_content = content.decode(enc)
            # print(f"S'ha detectat l'encodificació: {enc}")
            break
        except Exception:
            continue
            
    if decoded_content is None:
        raise ValueError("No s'ha pogut determinar l'encodificació del fitxer GEDCOM (prova a desar-lo com a UTF-8).")
    
    # Rewrite original temp file as utf-8-sig
    with open(file_path, 'w', encoding='utf-8-sig', errors='replace') as f:
        f.write(decoded_content)

def load_gedcom(file_path):
    """Loads a GEDCOM file and returns the parser and a list of all individuals."""
    _ensure_utf8_sig(file_path)
    parser = Parser()
    parser.parse_file(file_path)
    individuals = [e for e in parser.get_root_child_elements() if isinstance(e, IndividualElement)]
    return parser, individuals

def format_name(person):
    if not person:
        return "Desconegut"
    first, last = person.get_name()
    if first and last:
        return f"{first} {last}"
    return first or last or "Desconegut"

def get_person_details(person):
    if not person:
        return {}
    
    b_date, b_place, _ = person.get_birth_data()
    d_date, d_place, _ = person.get_death_data()
    
    if b_place: b_place = b_place.strip(", ")
    if d_place: d_place = d_place.strip(", ")

    gender = "U"
    try:
        g = person.get_gender()
        if g in ("M", "F"):
            gender = g
    except Exception:
        pass

    return {
        "id": person.get_pointer(),
        "name": format_name(person),
        "gender": gender,
        "birth_date": b_date or "",
        "birth_place": b_place or "",
        "death_date": d_date or "",
        "death_place": d_place or ""
    }

def collect_tree_data(parser, root_person, direction="Both", max_depth=3):
    """
    Traverses the family tree and extracts nodes and edges.

    Returns:
      all_nodes: list of node dicts, each with:
        - type="indi": {id, type, main, spouses:[{details, marriage_num, fam_id}],
                        has_multiple_marriages}
        - type="fam":  {id, type, husband, wife}
      edges: list of {from_id, to_id, label} dicts
    """
    indi_nodes = {}    # indi_id -> node_data
    fam_nodes  = {}    # fam_id  -> node_data
    edge_set   = set()
    edges      = []

    root_id = root_person.get_pointer()

    def add_edge(from_id, to_id, label=""):
        key = (from_id, to_id, label)
        if key not in edge_set:
            edge_set.add(key)
            edges.append({"from_id": from_id, "to_id": to_id, "label": label})

    # ── INDI nodes (descendants) ─────────────────────────────────────────────

    def ensure_indi_node(person):
        if not person:
            return None
        pid = person.get_pointer()
        if pid not in indi_nodes:
            indi_nodes[pid] = {
                "id": pid,
                "type": "indi",
                "main": get_person_details(person),
                "spouses": [],
                "has_multiple_marriages": False,
            }
        return pid

    def traverse_descendants(person, current_depth):
        if not person or current_depth > max_depth:
            return
        main_id = ensure_indi_node(person)
        node = indi_nodes[main_id]

        if current_depth >= max_depth:
            return

        families = list(parser.get_families(person, "FAMS"))
        marriage_count = len(families)
        existing_fam_ids = {s["fam_id"] for s in node["spouses"]}

        for marriage_num, fam in enumerate(families, start=1):
            fam_ptr = fam.get_pointer()
            fam_element = parser.get_element_dictionary().get(fam_ptr)
            if not fam_element:
                continue

            husb_list = parser.get_family_members(fam_element, "HUSB")
            wife_list = parser.get_family_members(fam_element, "WIFE")

            spouse_person = None
            if husb_list and husb_list[0].get_pointer() != main_id:
                spouse_person = husb_list[0]
            elif wife_list and wife_list[0].get_pointer() != main_id:
                spouse_person = wife_list[0]

            # Embed spouse into main node (only once per family)
            if fam_ptr not in existing_fam_ids:
                spouse_details = get_person_details(spouse_person) if spouse_person else None
                node["spouses"].append({
                    "details": spouse_details,
                    "marriage_num": marriage_num,
                    "fam_id": fam_ptr,
                })
                existing_fam_ids.add(fam_ptr)

            children = parser.get_family_members(fam_element, "CHIL")
            edge_label = f"({marriage_num})" if marriage_count > 1 else ""

            for child in children:
                add_edge(main_id, child.get_pointer(), edge_label)
                traverse_descendants(child, current_depth + 1)

        node["has_multiple_marriages"] = len(node["spouses"]) > 1

    # ── FAM nodes (ancestors) ────────────────────────────────────────────────

    def traverse_ancestors(child_node_id, person_element, current_depth):
        """Each ancestor couple becomes one FAM node."""
        if not person_element or current_depth >= max_depth:
            return

        for fam in parser.get_families(person_element, "FAMC"):
            fam_ptr = fam.get_pointer()
            fam_element = parser.get_element_dictionary().get(fam_ptr)
            if not fam_element:
                continue

            already_existed = fam_ptr in fam_nodes

            if not already_existed:
                husb_list = parser.get_family_members(fam_element, "HUSB")
                wife_list = parser.get_family_members(fam_element, "WIFE")
                husb = husb_list[0] if husb_list else None
                wife = wife_list[0] if wife_list else None

                fam_nodes[fam_ptr] = {
                    "id": fam_ptr,
                    "type": "fam",
                    "husband": get_person_details(husb) if husb else None,
                    "wife": get_person_details(wife) if wife else None,
                }

                # Recurse: look for grandparents of both sides
                if husb:
                    traverse_ancestors(fam_ptr, husb, current_depth + 1)
                if wife:
                    traverse_ancestors(fam_ptr, wife, current_depth + 1)

            add_edge(fam_ptr, child_node_id, "")

    # ── Run traversal ────────────────────────────────────────────────────────

    if direction in ["Descendants", "Both"]:
        traverse_descendants(root_person, 0)

    if direction in ["Ancestors", "Both"]:
        ensure_indi_node(root_person)
        traverse_ancestors(root_id, root_person, 0)

    # Ensure root always present
    ensure_indi_node(root_person)

    all_nodes = list(indi_nodes.values()) + list(fam_nodes.values())
    return all_nodes, edges
