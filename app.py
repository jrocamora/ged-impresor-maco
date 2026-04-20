import streamlit as st
import os
import tempfile
from parser import load_gedcom, collect_tree_data, format_name
from renderer import generate_graph, render_to_svg, render_to_pdf, THEMES

# ──────────────────────────────────────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Arbre Genealògic — Impressió A4",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# Light Theme CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ── Main background ── */
    .stApp {
        background-color: #f4f6f9;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #dde3ed;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
    }

    /* ── Sidebar text clearly dark ── */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #1e293b !important;
    }

    /* NOTE: DO NOT set font-family on .stApp or any broad selector —
       it cascades into Streamlit's icon spans and breaks Material Symbols ligatures. */


    /* ── Sidebar section headings ── */
    .sidebar-heading {
        color: #1e3a5f;
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin: 16px 0 8px 0;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    .sidebar-divider {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 12px 0;
    }

    /* ── Main title ── */
    .main-title {
        color: #1e3a5f;
        font-size: 2rem;
        font-weight: 700;
        font-family: 'Inter', 'Segoe UI', sans-serif;
        letter-spacing: -0.5px;
        margin-bottom: 0;
        padding-top: 0.5rem;
    }
    .main-subtitle {
        color: #64748b;
        font-size: 0.95rem;
        font-family: 'Inter', 'Segoe UI', sans-serif;
        margin-top: 4px;
        margin-bottom: 20px;
    }

    /* ── Section headings ── */
    .section-heading {
        color: #1e3a5f;
        font-size: 1.05rem;
        font-weight: 600;
        font-family: 'Inter', 'Segoe UI', sans-serif;
        margin-top: 24px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* ── Viewer wrapper ── */
    .viewer-wrap {
        border: 1px solid #dde3ed;
        border-radius: 10px;
        overflow: hidden;
        background: #ffffff;
        box-shadow: 0 2px 12px rgba(30,58,95,0.07);
    }

    /* ── Download buttons ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8f 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
        padding: 0.45rem 1.4rem !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 2px 8px rgba(30,58,95,0.25) !important;
        letter-spacing: 0.2px !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 16px rgba(30,58,95,0.35) !important;
    }

    /* ── Alerts ── */
    .stAlert {
        border-radius: 8px !important;
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
    }

    /* ── Footer ── */
    .app-footer {
        text-align: center;
        color: #94a3b8;
        font-size: 0.8rem;
        margin-top: 48px;
        padding: 16px 0;
        border-top: 1px solid #e2e8f0;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* ── Welcome box ── */
    .welcome-box {
        text-align: center;
        padding: 80px 20px;
        background: #ffffff;
        border: 1px solid #dde3ed;
        border-radius: 12px;
        margin-top: 20px;
        box-shadow: 0 2px 12px rgba(30,58,95,0.06);
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Interactive SVG Viewer (zoom + pan)
# ──────────────────────────────────────────────────────────────────────────────
def render_interactive_viewer(svg_content):
    """Renders an interactive SVG viewer with zoom/pan controls."""
    return f"""
    <div id="tree-viewer-wrapper" style="width:100%; font-family:'Inter','Segoe UI',sans-serif;">

        <!-- Toolbar -->
        <div style="
            display:flex; align-items:center; gap:8px;
            padding:8px 14px;
            background:#f0f4f8;
            border-bottom:1px solid #dde3ed;
        ">
            <button onclick="zoomOut()" id="btn-zoom-out" style="
                background:#ffffff; color:#1e3a5f; border:1px solid #c8d4e0;
                border-radius:6px; width:32px; height:32px; font-size:17px;
                cursor:pointer; line-height:1; transition:all 0.15s;
            " title="Reduir (-)">−</button>

            <input id="zoomRange" type="range" min="10" max="400" value="100"
                oninput="setZoom(this.value)"
                style="width:160px; height:5px; accent-color:#1e3a5f; cursor:pointer;"/>

            <button onclick="zoomIn()" id="btn-zoom-in" style="
                background:#ffffff; color:#1e3a5f; border:1px solid #c8d4e0;
                border-radius:6px; width:32px; height:32px; font-size:17px;
                cursor:pointer; line-height:1; transition:all 0.15s;
            " title="Augmentar (+)">+</button>

            <span id="zoomLabel" style="
                color:#1e3a5f; font-size:12px; font-weight:600;
                min-width:42px; text-align:center; font-family:'Inter',sans-serif;
            ">100%</span>

            <div style="width:1px; height:20px; background:#dde3ed; margin:0 4px;"></div>

            <button onclick="resetZoom()" style="
                background:#ffffff; color:#64748b; border:1px solid #c8d4e0;
                border-radius:6px; padding:4px 10px; font-size:12px;
                cursor:pointer; transition:all 0.15s; font-family:'Inter',sans-serif;
            " title="Reset 100%">Reset</button>

            <button onclick="fitToWindow()" style="
                background:#ffffff; color:#64748b; border:1px solid #c8d4e0;
                border-radius:6px; padding:4px 10px; font-size:12px;
                cursor:pointer; transition:all 0.15s; font-family:'Inter',sans-serif;
            " title="Ajustar a la finestra">Ajustar ⤢</button>

            <span style="margin-left:auto; color:#94a3b8; font-size:11px; font-family:'Inter',sans-serif;">
                🖱 Roda = zoom &nbsp;·&nbsp; Arrossega = moure
            </span>
        </div>

        <!-- SVG Viewport -->
        <div id="svgViewport" style="
            overflow:auto; background:#fafbfd;
            cursor:grab; height:620px; position:relative;
        ">
            <div id="svgContainer" style="
                transform-origin:0 0;
                transform:scale(1);
                display:inline-block;
                padding:24px;
                min-width:100%;
            ">
                {svg_content}
            </div>
        </div>
    </div>

    <script>
        let currentZoom = 100;
        const container  = document.getElementById('svgContainer');
        const viewport   = document.getElementById('svgViewport');
        const zoomRange  = document.getElementById('zoomRange');
        const zoomLabel  = document.getElementById('zoomLabel');
        const svgEl      = container.querySelector('svg');

        if (svgEl) {{
            // Remove hardcoded width/height to make it fluid
            svgEl.removeAttribute('width');
            svgEl.removeAttribute('height');
            svgEl.style.width    = '100%';
            svgEl.style.height   = 'auto';
            svgEl.style.display  = 'block';
            svgEl.style.maxWidth = 'none';
            
            // Auto-fit on first load if possible
            setTimeout(fitToWindow, 100);
        }}

        function setZoom(val) {{
            currentZoom = Math.round(Math.max(10, Math.min(400, parseInt(val))));
            container.style.transform = 'scale(' + (currentZoom / 100) + ')';
            zoomRange.value     = currentZoom;
            zoomLabel.textContent = currentZoom + '%';
        }}

        function zoomIn()    {{ setZoom(currentZoom + 15); }}
        function zoomOut()   {{ setZoom(currentZoom - 15); }}
        function resetZoom() {{ setZoom(100); }}

        function fitToWindow() {{
            if (!svgEl) return;
            const svgW = svgEl.viewBox?.baseVal?.width  || svgEl.width?.baseVal?.value  || 800;
            const svgH = svgEl.viewBox?.baseVal?.height || svgEl.height?.baseVal?.value || 600;
            const vpW  = viewport.clientWidth  - 48;
            const vpH  = viewport.clientHeight - 48;
            const fitZ = Math.min((vpW / svgW) * 100, (vpH / svgH) * 100);
            setZoom(fitZ);
        }}

        /* Wheel zoom */
        viewport.addEventListener('wheel', function(e) {{
            e.preventDefault();
            setZoom(currentZoom + (e.deltaY > 0 ? -10 : 10));
        }}, {{ passive: false }});

        /* Keyboard shortcuts */
        document.addEventListener('keydown', function(e) {{
            if (e.key === '=' || e.key === '+') {{ e.preventDefault(); zoomIn(); }}
            if (e.key === '-')                  {{ e.preventDefault(); zoomOut(); }}
            if (e.key === '0')                  {{ e.preventDefault(); resetZoom(); }}
        }});

        /* Pan with drag */
        let panning = false, startX, startY, scrollL, scrollT;

        viewport.addEventListener('mousedown', function(e) {{
            panning = true;
            viewport.style.cursor = 'grabbing';
            startX  = e.pageX - viewport.offsetLeft;
            startY  = e.pageY - viewport.offsetTop;
            scrollL = viewport.scrollLeft;
            scrollT = viewport.scrollTop;
        }});
        viewport.addEventListener('mouseup',    function() {{ panning = false; viewport.style.cursor = 'grab'; }});
        viewport.addEventListener('mouseleave', function() {{ panning = false; viewport.style.cursor = 'grab'; }});
        viewport.addEventListener('mousemove',  function(e) {{
            if (!panning) return;
            e.preventDefault();
            const dx = e.pageX - viewport.offsetLeft - startX;
            const dy = e.pageY - viewport.offsetTop  - startY;
            viewport.scrollLeft = scrollL - dx * 1.4;
            viewport.scrollTop  = scrollT - dy * 1.4;
        }});

        /* Auto-fit on load */
        window.addEventListener('load', function() {{ setTimeout(fitToWindow, 100); }});
    </script>
    """


# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🌳 Arbre Genealògic</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="main-subtitle">Puja un fitxer <code>.ged</code>, selecciona una persona arrel '
    'i personalitza l\'arbre per imprimir en A4.</p>',
    unsafe_allow_html=True
)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — File upload
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown('<p class="sidebar-heading">📁 Fitxer GEDCOM</p>', unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader(
    "Puja el fitxer .ged", type=["ged"], label_visibility="collapsed"
)

if uploaded_file is not None:
    # Use uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ged") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    try:
        parser, individuals = load_gedcom(tmp_path)
        st.session_state["data"] = (parser, individuals)
    finally:
        os.remove(tmp_path)



# ──────────────────────────────────────────────────────────────────────────────
# Main content
# ──────────────────────────────────────────────────────────────────────────────
if "data" in st.session_state and st.session_state["data"][1]:
    parser, individuals = st.session_state["data"]

    # ── Tree Configuration ────────────────────────────────────────────────────
    st.sidebar.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    st.sidebar.markdown('<p class="sidebar-heading">🧬 Configuració de l\'arbre</p>', unsafe_allow_html=True)

    options = {
        ind.get_pointer(): f"{format_name(ind)} ({ind.get_pointer()})"
        for ind in individuals
    }
    selected_id = st.sidebar.selectbox(
        "Persona arrel (Cerca escrivint)",
        options=list(options.keys()),
        format_func=lambda x: options[x]
    )
    selected_person = next((i for i in individuals if i.get_pointer() == selected_id), None)

    dir_options = {"Descendants": "Descendents", "Ancestors": "Avantpassats", "Both": "Ambdós"}
    direction = st.sidebar.selectbox(
        "Direcció",
        options=list(dir_options.keys()),
        format_func=lambda x: dir_options[x]
    )
    layout    = st.sidebar.selectbox("Disposició", ["Horizontal", "Vertical"])
    max_depth = st.sidebar.slider("Profunditat (generacions)", min_value=1, max_value=10, value=3)

    # ── Appearance ───────────────────────────────────────────────────────────
    st.sidebar.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    st.sidebar.markdown('<p class="sidebar-heading">🎨 Aparença</p>', unsafe_allow_html=True)

    theme_name       = st.sidebar.selectbox("Tema de colors", list(THEMES.keys()))
    use_gender_colors = st.sidebar.checkbox(
        "Colors per gènere",
        value=True,
        help="Desactiva per obtenir un arbre en blanc i negre, ideal per impressió."
    )
    rounded_corners = st.sidebar.checkbox("Vores arrodonides", value=False)
    compact_mode    = st.sidebar.checkbox("Mode compacte", value=False, help="Redueix l'espai entre caixes i generacions per maximitzar l'espai.")
    node_width = st.sidebar.slider("Amplada dels nodes (px)", min_value=120, max_value=400, value=180, step=10)

    # ── Detail toggles ────────────────────────────────────────────────────────
    st.sidebar.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    st.sidebar.markdown('<p class="sidebar-heading">📋 Detalls</p>', unsafe_allow_html=True)

    show_birth    = st.sidebar.checkbox("Data de naixement",  value=True)
    show_death    = st.sidebar.checkbox("Data de defunció",   value=True)
    show_location = st.sidebar.checkbox("Llocs",             value=True)

    # ── Generate ──────────────────────────────────────────────────────────────
    if selected_person:
        nodes, edges = collect_tree_data(
            parser, selected_person,
            direction=direction, max_depth=max_depth
        )

        node_count = len(nodes)
        if node_count > 60:
            st.warning(f"⚠️ L'arbre és gran ({node_count} nodes). Pot ser massa dens per un A4.")
        elif node_count > 30:
            st.info(f"ℹ️ L'arbre té {node_count} nodes. La llegibilitat en A4 pot ser justa.")
        else:
            st.success(f"✅ L'arbre té {node_count} nodes. Bona mida per impressió A4.")

        dot         = generate_graph(
            nodes, edges,
            layout=layout,
            show_birth=show_birth,
            show_death=show_death,
            show_location=show_location,
            theme_name=theme_name,
            use_gender_colors=use_gender_colors,
            root_id=selected_id,
            rounded_corners=rounded_corners,
            node_width=node_width,
            compact_mode=compact_mode
        )
        svg_content = render_to_svg(dot)

        # ── Interactive preview ───────────────────────────────────────────────
        st.markdown('<p class="section-heading">🔍 Previsualització interactiva</p>',
                    unsafe_allow_html=True)

        if "Error:" in svg_content:
            st.error(
                "❌ Graphviz no trobat al sistema. "
                "Instal·la'l des de https://graphviz.org/download/ i afegeix-lo al PATH."
            )
            with st.expander("🛠️ Diagnòstic per a Streamlit Cloud"):
                import shutil
                dot_path = shutil.which("dot")
                st.write(f"**Cerca de 'dot':** {dot_path if dot_path else 'No trobat'}")
                st.write("**PATH actual:**")
                st.code(os.environ.get("PATH", ""))
                st.info("💡 Si 'dot' no apareix i ja has pujat el fitxer `packages.txt`, ves al dashboard de Streamlit Cloud i fes un **'Reboot App'** des del menú de configuració.")
        else:
            viewer_html = render_interactive_viewer(svg_content)
            st.components.v1.html(viewer_html, height=690, scrolling=False)

        # ── Export ────────────────────────────────────────────────────────────
        if "Error:" not in svg_content:
            st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
            st.markdown('<p class="section-heading">💾 Exportar</p>', unsafe_allow_html=True)

            safe_name = format_name(selected_person).replace(" ", "_").replace("/", "").replace("\\", "")
            d_name = dir_options[direction]
            export_base_name = f"Arbre_{safe_name}_{d_name}"

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                st.download_button(
                    label="📥 Descarregar SVG",
                    data=svg_content,
                    file_name=f"{export_base_name}.svg",
                    mime="image/svg+xml"
                )
            with col2:
                pdf_path = os.path.join(tempfile.gettempdir(), f"{export_base_name}")
                if render_to_pdf(dot, pdf_path):
                    try:
                        with open(pdf_path + ".pdf", "rb") as pdf_file:
                            st.download_button(
                                label="📥 Descarregar PDF",
                                data=pdf_file.read(),
                                file_name=f"{export_base_name}.pdf",
                                mime="application/pdf"
                            )
                    finally:
                        if os.path.exists(pdf_path + ".pdf"):
                            os.remove(pdf_path + ".pdf")
                else:
                    st.error("No s'ha pogut generar el PDF.")

    # Footer
    st.markdown(
        '<div class="app-footer">🌳 Arbre Genealògic · Fet amb 💙 per imprimir la teva història familiar</div>',
        unsafe_allow_html=True
    )

    # ── JS Hack: Select all text on Selectbox focus ──
    st.components.v1.html("""
        <script>
            function setupSelectAll() {
                const innerDoc = window.parent.document;
                const inputs = innerDoc.querySelectorAll('input[data-testid="stSelectboxVirtualFocusWidget"], [role="combobox"] input');
                
                inputs.forEach(input => {
                    if (input.dataset.handledSelectAll) return;
                    input.dataset.handledSelectAll = "true";
                    
                    input.addEventListener('focus', function() {
                        setTimeout(() => {
                            this.select();
                        }, 50);
                    });
                });
            }
            // Periodically check for new selectboxes
            setInterval(setupSelectAll, 1000);
        </script>
    """, height=0)

else:
    # Welcome state
    st.markdown("""
    <div class="welcome-box">
        <div style="font-size:56px; margin-bottom:16px;">🌳</div>
        <div style="font-size:1.25rem; font-weight:600; color:#1e3a5f;
                    font-family:'Inter','Segoe UI',sans-serif;">
            Puja un fitxer GEDCOM per començar
        </div>
        <div style="font-size:0.9rem; color:#64748b; margin-top:8px;
                    font-family:'Inter','Segoe UI',sans-serif;">
            Utilitza el panell lateral per pujar el teu fitxer <code>.ged</code>
        </div>
    </div>
    """, unsafe_allow_html=True)
