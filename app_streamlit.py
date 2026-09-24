"""
Signals EMEA Hackathon 2026 — Unified Streamlit Dashboard
Multi-tab interactive application featuring:
1. Signals Tenant Overview & Connectivity Health
2. Molecule Explorer & Chemoinformatics (RDKit 2D depiction & Signals API drawing fetch)
3. Signals REST API Sandbox & Explorer (Interactive live/mock endpoint runner)
4. AI Scientific Assistant (Google Gemini 3.6 Flash)
"""
import os
import sys
import json
import io
import streamlit as st

# Ensure repository root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.signals_client import SignalsClient
from backend.ai_client import AIClient

# Page configuration
st.set_page_config(
    page_title="Signals EMEA Hackathon 2026",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom branding CSS (Revvity Teal palette)
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #00707d;
        margin-bottom: 4px;
    }
    .sub-header {
        font-size: 15px;
        color: #555;
        margin-bottom: 18px;
    }
    .status-badge-ok {
        background-color: #eef6ef;
        color: #2e7d32;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 13px;
        display: inline-block;
    }
    .status-badge-mock {
        background-color: #fdf6e6;
        color: #8a6100;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 13px;
        display: inline-block;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 12px 16px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Clients
@st.cache_resource
def get_signals_client():
    return SignalsClient()

@st.cache_resource
def get_ai_client():
    return AIClient()

signals_client = get_signals_client()
ai_client = get_ai_client()

# Sidebar: Tenant & Environment Status
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Revvity_Logo.svg/320px-Revvity_Logo.svg.png", width=180)
    st.markdown("### Environment Controls")
    
    conn_status = signals_client.check_connection()
    if conn_status.get("status") == "connected":
        st.markdown('<span class="status-badge-ok">✓ Live Signals Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge-mock">⚡ Offline Mock Mode Active</span>', unsafe_allow_html=True)
        
    st.caption(f"**Tenant:** `{signals_client.base_url}`")
    
    st.divider()
    st.markdown("### AI Copilot Status")
    ai_status = ai_client.check_status()
    st.write(f"**Model:** `{ai_status.get('model')}`")
    st.write(f"**Provider:** {ai_status.get('provider')}")
    st.write(f"**Key Configured:** {'Yes' if ai_status.get('keyConfigured') else 'Mock Simulator'}")
    
    st.divider()
    st.markdown("### Quick Resources")
    st.markdown("📖 [API Catalog](docs/API_CATALOG.md)")
    st.markdown("⚡ [Signals Developer Cheat Sheet](docs/SIGNALS_DEVELOPER_CHEAT_SHEET.md)")

# Main Header
st.markdown('<div class="main-header">Revvity Signals EMEA Hackathon 2026 — Universal Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Integrated Rapid Prototyping Platform for Signals Notebook REST APIs, RDKit, and Google GenAI</div>', unsafe_allow_html=True)

# Tabs
tab_overview, tab_molecule, tab_sandbox, tab_ai = st.tabs([
    "📋 Signals Overview",
    "🔬 Molecule Explorer",
    "⚡ API Sandbox & Explorer",
    "🤖 AI Assistant"
])

# =========================================================================
# TAB 1: SIGNALS OVERVIEW & EXPERIMENTS
# =========================================================================
with tab_overview:
    st.subheader("Tenant Status & Experiments")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Tenant Mode", value="Mock Simulator" if signals_client.mock_mode else "Live Cloud")
    with col2:
        try:
            exps = signals_client.list_experiments(limit=50)
            st.metric(label="Accessible Experiments", value=len(exps))
        except Exception:
            exps = []
            st.metric(label="Accessible Experiments", value="0")
    with col3:
        st.metric(label="Target Host", value="Signals Notebook v1.0")
        
    st.markdown("#### Experiment Notebooks")
    if exps:
        exp_table = []
        for e in exps:
            exp_table.append({
                "Entity ID (EID)": e.get("eid"),
                "Experiment Name": e.get("name"),
                "Last Modified": e.get("modifiedAt", "N/A")
            })
        st.dataframe(exp_table, use_container_width=True)
    else:
        st.info("No experiments found or unable to connect.")

    # Quick create experiment form
    with st.expander("➕ Create New Experiment Notebook"):
        with st.form("create_exp_form"):
            new_title = st.text_input("Experiment Title", value="EXP-2026-HACK: Novel Synthesis Pilot")
            new_desc = st.text_area("Description / Objective", value="Created via Signals Hackathon Starter Streamlit UI")
            submitted = st.form_submit_button("Create Experiment")
            if submitted:
                try:
                    res = signals_client.create_experiment(new_title, new_desc)
                    st.success(f"Experiment created successfully! ID: `{res.get('id')}`")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to create experiment: {exc}")

# =========================================================================
# TAB 2: MOLECULE EXPLORER & CHEMOINFORMATICS
# =========================================================================
with tab_molecule:
    st.subheader("Chemical Structure & Property Explorer")
    st.caption("Fetch drawings directly from Revvity Signals Notebook, parse SMILES with RDKit, and calculate physicochemical descriptors.")

    # Ingress Source Selector
    ingress_mode = st.radio("Structure Source:", ["Fetch from Signals API", "Manual SMILES Entry"], horizontal=True)
    
    current_smiles = "CC(=O)Oc1ccccc1C(=O)O"
    raw_svg_content = None

    if ingress_mode == "Fetch from Signals API":
        c_in1, c_in2, c_in3 = st.columns([2, 1, 1])
        with c_in1:
            asset_id = st.text_input("Signals Material / Asset Batch ID", value="material:aspirin-batch-001", help="Enter a material ID, container ID, or assetBatchId.")
        with c_in2:
            format_choice = st.selectbox("Format", ["smiles", "svg", "mol"])
        with c_in3:
            st.write("")
            st.write("")
            fetch_btn = st.button("📥 Fetch Drawing", type="primary")

        if fetch_btn:
            with st.spinner("Fetching drawing from Signals REST API..."):
                try:
                    drawing_data = signals_client.get_chemical_drawing(asset_id, format=format_choice)
                    if format_choice == "svg":
                        raw_svg_content = drawing_data
                        st.success(f"Retrieved SVG vector drawing from Signals ({len(drawing_data)} bytes)!")
                    elif format_choice == "smiles":
                        current_smiles = drawing_data.strip()
                        st.success(f"Retrieved SMILES from Signals: `{current_smiles}`")
                    else:
                        st.code(drawing_data, language="text")
                except Exception as e:
                    st.error(f"Error fetching drawing from Signals: {e}")
    else:
        current_smiles = st.text_input("Enter SMILES String", value="CC(=O)Oc1ccccc1C(=O)O")

    st.divider()

    # RDKit Chemoinformatics Render
    rdkit_available = False
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, Draw, Lipinski
        rdkit_available = True
    except ImportError:
        st.warning("RDKit is not installed in the local environment; running in fallback mode.")

    col_img, col_props = st.columns([1, 1])

    if raw_svg_content:
        with col_img:
            st.markdown("#### Signals ChemDraw Vector Render")
            st.markdown(raw_svg_content, unsafe_allow_html=True)
    elif rdkit_available and current_smiles:
        mol = Chem.MolFromSmiles(current_smiles)
        with col_img:
            st.markdown("#### 2D Structure Depiction (RDKit)")
            if mol:
                img = Draw.MolToImage(mol, size=(380, 260))
                st.image(img, use_container_width=True)
            else:
                st.error("Invalid SMILES string could not be parsed by RDKit.")

        with col_props:
            st.markdown("#### Calculated Physicochemical Properties")
            if mol:
                mw = round(Descriptors.MolWt(mol), 2)
                logp = round(Descriptors.MolLogP(mol), 2)
                tpsa = round(Descriptors.TPSA(mol), 2)
                hbd = Lipinski.NumHDonors(mol)
                hba = Lipinski.NumHAcceptors(mol)
                rotb = Lipinski.NumRotatableBonds(mol)
                formula = Chem.rdMolDescriptors.CalcMolFormula(mol)

                m1, m2 = st.columns(2)
                m1.metric("Formula", formula)
                m2.metric("Molecular Weight", f"{mw} g/mol")
                m3, m4 = st.columns(2)
                m3.metric("LogP", logp)
                m4.metric("TPSA", f"{tpsa} Å²")
                m5, m6 = st.columns(2)
                m5.metric("H-Bond Donors / Acceptors", f"{hbd} / {hba}")
                m6.metric("Rotatable Bonds", rotb)
            else:
                st.info("Enter a valid SMILES structure to compute molecular descriptors.")

# =========================================================================
# TAB 3: SIGNALS API SANDBOX & EXPLORER
# =========================================================================
with tab_sandbox:
    st.subheader("⚡ Signals REST API Sandbox")
    st.caption("Interactive test harness to test Signals API operations with instant curl and JSON:API inspection.")

    endpoint_presets = [
        "GET /materials/{assetBatchId}/drawing (Chemical Drawing)",
        "GET /stoichiometry/{eid} (Reaction Reactants & Products)",
        "GET /entities (List Accessible Notebooks)",
        "GET /materials/bulk (Search Inventory & Reagents)",
        "GET /entities/{eid}/children (List Child Elements)",
        "POST /entities (Create Experiment)"
    ]

    selected_op = st.selectbox("Select Signals API Endpoint to Test:", endpoint_presets)

    c_param1, c_param2 = st.columns(2)
    with c_param1:
        if "drawing" in selected_op:
            target_id = st.text_input("assetBatchId / Material ID", value="material:aspirin-batch-001")
            format_p = st.selectbox("format query param", ["smiles", "svg", "mol", "cdxml", "inchi"])
        elif "stoichiometry" in selected_op:
            target_id = st.text_input("drawing_eid", value="chemicalDrawing:e323ff17-15c4-4706-9bf3-7f2e12a00099")
        elif "bulk" in selected_op:
            query_str = st.text_input("filter[query]", value="Phenylboronic acid")
            limit_p = st.number_input("page[limit]", min_value=1, max_value=50, value=5)
        elif "children" in selected_op:
            target_id = st.text_input("parent_eid", value="experiment:e323ff17-15c4-4706-9bf3-7f2e12a40001")
        elif "POST /entities" in selected_op:
            exp_name = st.text_input("attributes.name", value="EXP-2026-HACK: Suzuki Screen 4B")
            exp_desc = st.text_input("attributes.description", value="Automated API creation")
        else:
            limit_p = st.number_input("page[limit]", min_value=1, max_value=50, value=5)

    with c_param2:
        st.markdown("#### Generated cURL Command")
        base = signals_client.base_url
        if "drawing" in selected_op:
            curl_cmd = f"curl -X GET '{base}/materials/{target_id}/drawing?format={format_p}' \
  -H 'x-api-key: $SIGNALS_API_KEY'"
        elif "stoichiometry" in selected_op:
            curl_cmd = f"curl -X GET '{base}/stoichiometry/{target_id}' \
  -H 'x-api-key: $SIGNALS_API_KEY' \
  -H 'Accept: application/vnd.api+json'"
        elif "bulk" in selected_op:
            curl_cmd = f"curl -X GET '{base}/materials/bulk?filter[query]={query_str}&page[limit]={limit_p}' \
  -H 'x-api-key: $SIGNALS_API_KEY'"
        elif "children" in selected_op:
            curl_cmd = f"curl -X GET '{base}/entities/{target_id}/children' \
  -H 'x-api-key: $SIGNALS_API_KEY'"
        elif "POST /entities" in selected_op:
            curl_cmd = f"curl -X POST '{base}/entities' \
  -H 'x-api-key: $SIGNALS_API_KEY' \
  -H 'Content-Type: application/vnd.api+json' \
  -d '{{"data": {{"type": "experiment", "attributes": {{"name": "{exp_name}"}}}}}}'"
        else:
            curl_cmd = f"curl -X GET '{base}/entities?filter[type]=experiment&page[limit]={limit_p}' \
  -H 'x-api-key: $SIGNALS_API_KEY'"

        st.code(curl_cmd, language="bash")

    if st.button("🚀 Execute API Request", type="primary"):
        with st.spinner("Executing request..."):
            try:
                if "drawing" in selected_op:
                    res_payload = signals_client.get_chemical_drawing(target_id, format=format_p)
                elif "stoichiometry" in selected_op:
                    res_payload = signals_client.get_stoichiometry(target_id)
                elif "bulk" in selected_op:
                    res_payload = signals_client.search_materials(query_str, limit=limit_p)
                elif "children" in selected_op:
                    res_payload = signals_client.list_child_entities(target_id)
                elif "POST /entities" in selected_op:
                    res_payload = signals_client.create_experiment(exp_name, exp_desc)
                else:
                    res_payload = signals_client.list_experiments(limit=limit_p)

                st.success("200 OK — Request Succeeded!")
                if isinstance(res_payload, (dict, list)):
                    st.json(res_payload)
                else:
                    st.code(res_payload, language="text")
            except Exception as e:
                st.error(f"API Execution Error: {e}")

# =========================================================================
# TAB 4: AI EXPERIMENT ASSISTANT
# =========================================================================
with tab_ai:
    st.subheader("🤖 AI Scientific Lab Assistant")
    st.caption("Powered by Google Gemini 3.6 Flash via unified AIClient.")

    quick_prompts = [
        "Summarize the objective and procedure for EXP-2026-081 (Suzuki Catalyst Screening).",
        "Suggest optimal reaction temperature and base for cross-coupling of 4-Bromobenzonitrile.",
        "Generate a compliance validation checklist for new chemical drawing entities."
    ]
    
    preset_choice = st.selectbox("Quick Prompts:", ["Custom Prompt"] + quick_prompts)
    default_prompt_val = "" if preset_choice == "Custom Prompt" else preset_choice

    user_query = st.text_area("Your Scientific Prompt:", value=default_prompt_val, height=100)
    
    if st.button("✨ Ask AI Assistant", type="primary"):
        if not user_query.strip():
            st.warning("Please enter a prompt first.")
        else:
            with st.spinner("Synthesizing response with Gemini 3.6 Flash..."):
                try:
                    ai_res = ai_client.generate_text(
                        prompt=user_query,
                        system_instruction="You are an expert cheminformatics and electronic lab notebook AI copilot for the Revvity Signals EMEA Hackathon 2026."
                    )
                    st.markdown("### AI Analysis")
                    st.markdown(ai_res.get("text", "No response text received."))
                    
                    with st.expander("Inspect Raw Metadata"):
                        st.json(ai_res)
                except Exception as err:
                    st.error(f"AI Generation Error: {err}")
