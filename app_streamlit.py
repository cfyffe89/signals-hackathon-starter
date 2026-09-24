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
    st.caption("Live integration: queries the Signals Search/Entities API for the last 20 chemical drawings, fetches SMILES, calculates RDKit descriptors, and performs medicinal chemistry analysis with Gemini 3.6 Flash.")

    # 1. Fetch the last 20 chemical drawings from Signals Notebook
    with st.spinner("Fetching latest chemical drawings from Signals Notebook..."):
        try:
            drawings = signals_client.list_chemical_drawings(limit=20)
        except Exception as e:
            st.error(f"Failed to query chemical drawings from Signals API: {e}")
            drawings = []

    current_smiles = "CC(=O)Oc1ccccc1C(=O)O"
    current_name = "Aspirin (Default)"
    current_id = "chemicalDrawing:cd-001"
    current_author = "Dr. Sarah Chen"
    current_modified = "Recent"
    current_notebook = "EXP-2026-081"

    if drawings:
        st.markdown(f"**Discovered {len(drawings)} Chemical Drawings in Tenant** (`GET /entities?filter[type]=chemicalDrawing&sort=-modifiedAt`):")
        drawing_options = [
            f"{i+1}. {d.get('name', 'Untitled')} [{d.get('id', 'N/A')}] — {d.get('formula', '')} ({d.get('notebook', 'Lab')})"
            for i, d in enumerate(drawings)
        ]
        selected_idx = st.selectbox(
            "Select Drawing to Inspect & Analyze:",
            range(len(drawings)),
            format_func=lambda i: drawing_options[i],
            help="Select one of the last 20 chemical drawings registered in Revvity Signals Notebook."
        )
        selected_drawing = drawings[selected_idx]
        current_smiles = selected_drawing.get("smiles", "CC(=O)Oc1ccccc1C(=O)O")
        current_name = selected_drawing.get("name", "Chemical Drawing")
        current_id = selected_drawing.get("id", "N/A")
        current_author = selected_drawing.get("author", "Scientist")
        current_modified = selected_drawing.get("modifiedAt", "N/A")
        current_notebook = selected_drawing.get("notebook", "General")

        # Metadata badges
        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        c_m1.caption(f"**Entity ID:** `{current_id}`")
        c_m2.caption(f"**Notebook:** `{current_notebook}`")
        c_m3.caption(f"**Author:** {current_author}")
        c_m4.caption(f"**Modified:** {current_modified[:10] if len(current_modified)>=10 else current_modified}")

    # Optional expander for manual SMILES or custom Asset Batch ID
    with st.expander("🛠️ Advanced: Custom Entity / Manual SMILES Lookup"):
        alt_mode = st.radio("Alternative Input:", ["Custom SMILES Entry", "Fetch Asset Batch by ID"], horizontal=True)
        if alt_mode == "Custom SMILES Entry":
            custom_s = st.text_input("Enter Custom SMILES String:", value=current_smiles)
            if custom_s.strip() and custom_s.strip() != current_smiles:
                current_smiles = custom_s.strip()
                current_name = f"Custom Structure ({current_smiles[:20]}...)"
                current_id = "custom:manual-smiles"
        else:
            col_b1, col_b2 = st.columns([3, 1])
            with col_b1:
                custom_aid = st.text_input("Asset Batch / Material ID", value="material:aspirin-batch-001")
            with col_b2:
                fetch_b_btn = st.button("Fetch Asset", type="secondary")
            if fetch_b_btn:
                try:
                    fetched_smiles = signals_client.get_chemical_drawing(custom_aid, format="smiles")
                    current_smiles = fetched_smiles.strip()
                    current_name = f"Material {custom_aid}"
                    current_id = custom_aid
                    st.success(f"Fetched SMILES for {custom_aid}: `{current_smiles}`")
                except Exception as ex:
                    st.error(f"Error fetching drawing: {ex}")

    st.divider()

    # RDKit Chemoinformatics Render & Properties
    rdkit_available = False
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, Draw, Lipinski
        rdkit_available = True
    except ImportError:
        pass

    mol = None
    mw = "N/A"
    logp = "N/A"
    tpsa = "N/A"
    hbd = "N/A"
    hba = "N/A"
    rotb = "N/A"
    formula = selected_drawing.get("formula", "N/A") if drawings else "N/A"

    col_img, col_props = st.columns([1, 1])

    if rdkit_available and current_smiles:
        try:
            mol = Chem.MolFromSmiles(current_smiles)
        except Exception:
            mol = None

    with col_img:
        st.markdown(f"#### 2D Chemical Structure: `{current_name}`")
        if mol:
            img = Draw.MolToImage(mol, size=(420, 280))
            st.image(img, use_container_width=True)
            st.caption(f"**Canonical SMILES:** `{current_smiles}`")
        elif not rdkit_available:
            st.info("ℹ️ **RDKit 2D Depiction**: RDKit will render interactive 2D structures inside the Linux Codespace container. Canonical SMILES:")
            st.code(current_smiles, language="text")
        else:
            st.error("Invalid SMILES string could not be parsed by RDKit.")
            st.code(current_smiles, language="text")

    with col_props:
        st.markdown("#### Physicochemical Descriptors")
        if mol:
            mw = round(Descriptors.MolWt(mol), 2)
            logp = round(Descriptors.MolLogP(mol), 2)
            tpsa = round(Descriptors.TPSA(mol), 2)
            hbd = Lipinski.NumHDonors(mol)
            hba = Lipinski.NumHAcceptors(mol)
            rotb = Lipinski.NumRotatableBonds(mol)
            formula = Chem.rdMolDescriptors.CalcMolFormula(mol)

            m1, m2 = st.columns(2)
            m1.metric("Molecular Formula", formula)
            m2.metric("Molecular Weight", f"{mw} g/mol")
            m3, m4 = st.columns(2)
            m3.metric("Calculated LogP", logp)
            m4.metric("Polar Surface Area (TPSA)", f"{tpsa} Å²")
            m5, m6 = st.columns(2)
            m5.metric("H-Bond Donors / Acceptors", f"{hbd} / {hba}")
            m6.metric("Rotatable Bonds", rotb)

            # Lipinski Rule of 5 check
            ro5_violations = sum([
                1 if mw > 500 else 0,
                1 if logp > 5 else 0,
                1 if hbd > 5 else 0,
                1 if hba > 10 else 0
            ])
            if ro5_violations == 0:
                st.success("✅ Lipinski Rule of 5: All criteria satisfied (High oral bioavailability potential)")
            else:
                st.warning(f"⚠️ Lipinski Rule of 5: {ro5_violations} violation(s) detected")
        else:
            m1, m2 = st.columns(2)
            m1.metric("Molecular Formula", formula)
            m2.metric("SMILES Length", len(current_smiles))
            st.info("Full RDKit descriptor calculation available in Codespace environment.")

    # AI Chemical Drawing Analysis Section
    st.divider()
    c_btn, c_note = st.columns([1, 2])
    with c_btn:
        analyze_clicked = st.button("✨ Analyze Drawing with Gemini", type="primary", use_container_width=True)
    with c_note:
        st.caption("Submits structure coordinates, formula, and physicochemical properties to **Gemini 3.6 Flash** for automated medicinal chemistry & ADMET evaluation.")

    if analyze_clicked:
        with st.spinner(f"Analyzing {current_name} with Gemini 3.6 Flash..."):
            chem_prompt = f"""You are an expert computational medicinal chemist and drug discovery consultant for Revvity Signals Notebook.
Please analyze the following chemical drawing entity retrieved from Signals Notebook:

- Entity Name: {current_name}
- Signals Entity ID: {current_id}
- Notebook Reference: {current_notebook}
- SMILES: {current_smiles}
- Molecular Formula: {formula}
- Molecular Weight: {mw} g/mol
- LogP: {logp}
- Polar Surface Area (TPSA): {tpsa} Å²
- H-Bond Donors: {hbd}
- H-Bond Acceptors: {hba}
- Rotatable Bonds: {rotb}

Please provide a structured, rigorous medicinal chemistry report with the following 4 sections:
1. **Chemical Classification & Pharmacophore**: Primary scaffold, heterocycles, key functional groups, and known biological targets / mechanism of action.
2. **Lipinski & Veber Drug-Likeness**: Evaluation against Lipinski Rule of 5 and Veber bioavailability metrics (violations, oral bioavailability prediction).
3. **ADMET & Safety Profile**: Predicted membrane permeability, metabolic clearance liabilities (CYP/esterase sites), blood-brain barrier tendencies, and structural alerts (PAINS).
4. **Lead Optimization & Synthetic SAR Strategies**: 2-3 specific, actionable chemical modifications to improve potency, metabolic stability, or target selectivity.
"""
            try:
                ai_res = ai_client.generate_text(
                    prompt=chem_prompt,
                    system_instruction="You are a senior medicinal chemistry AI assistant in Revvity Signals Notebook. Deliver concise, scientifically precise insights formatted in clean Markdown."
                )
                st.session_state[f"ai_chem_{current_id}"] = ai_res
            except Exception as e:
                st.error(f"AI Generation Error: {e}")

    # Display saved analysis if available
    saved_analysis = st.session_state.get(f"ai_chem_{current_id}")
    if saved_analysis:
        st.markdown(f"### 🧬 AI Medicinal Chemistry Assessment: `{current_name}`")
        st.caption(f"Synthesized by **{saved_analysis.get('source', 'Gemini 3.6 Flash')}**")
        st.markdown(saved_analysis.get("text", "No analysis text received."))

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
            curl_cmd = f"""curl -X GET '{base}/materials/{target_id}/drawing?format={format_p}' \\
  -H 'x-api-key: $SIGNALS_API_KEY'"""
        elif "stoichiometry" in selected_op:
            curl_cmd = f"""curl -X GET '{base}/stoichiometry/{target_id}' \\
  -H 'x-api-key: $SIGNALS_API_KEY' \\
  -H 'Accept: application/vnd.api+json'"""
        elif "bulk" in selected_op:
            curl_cmd = f"""curl -X GET '{base}/materials/bulk?filter[query]={query_str}&page[limit]={limit_p}' \\
  -H 'x-api-key: $SIGNALS_API_KEY'"""
        elif "children" in selected_op:
            curl_cmd = f"""curl -X GET '{base}/entities/{target_id}/children' \\
  -H 'x-api-key: $SIGNALS_API_KEY'"""
        elif "POST /entities" in selected_op:
            curl_cmd = f"""curl -X POST '{base}/entities' \\
  -H 'x-api-key: $SIGNALS_API_KEY' \\
  -H 'Content-Type: application/vnd.api+json' \\
  -d '{{"data": {{"type": "experiment", "attributes": {{"name": "{exp_name}"}}}}}}'"""
        else:
            curl_cmd = f"""curl -X GET '{base}/entities?filter[type]=experiment&page[limit]={limit_p}' \\
  -H 'x-api-key: $SIGNALS_API_KEY'"""

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
