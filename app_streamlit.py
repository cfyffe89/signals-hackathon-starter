"""Streamlit app: the "UI" half of the starter (port 8501).

Run:  streamlit run app_streamlit.py --server.port 8501
Tabs: Experiments (read + ask AI about one) · Chemistry (drawings, RDKit, structure search) ·
      Materials · Ask the Signals expert (API / integration Q&A from docs/signals).
"""
import streamlit as st

from backend import config  # noqa: F401  (loads .env / Codespaces secrets)
from backend.ai_client import AIClient
from backend.context import experiment_context, structure_context
from backend.knowledge import find_endpoints, knowledge_block, search_knowledge
from backend.signals_client import SignalsClient, SignalsError

st.set_page_config(page_title="Signals Hackathon Starter", page_icon="🧪", layout="wide")
sc, ai = SignalsClient(), AIClient()

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.title("Signals Starter")
    conn = sc.check_connection()
    st.write(f"**Signals:** {conn['status']}")
    st.caption(conn.get("tenant", ""))
    if conn["status"] == "error":
        st.error(conn.get("error", ""))
    status = ai.check_status()
    st.write(f"**AI:** {status['provider']} · {status['model']}")
    if sc.mock_mode or status["mockMode"]:
        st.info("Mock mode is on for anything without a key. Fill in `.env` (see README) to go live.")
    st.divider()
    try:
        notebooks = sorted(sc.list_notebooks(100), key=lambda n: (n["name"] or "").lower())
    except SignalsError as e:
        st.error(e); notebooks = []
    notebook = st.selectbox("Notebook (you write here)", notebooks, index=None,
                            placeholder="Choose your team notebook", format_func=lambda n: n["name"])
    st.divider()
    st.caption("Code: `app_streamlit.py` · API client: `backend/signals_client.py` · Knowledge: `docs/signals/`")


def show_answer(res: dict):
    st.markdown(res["text"])
    st.caption(f"— {res['source']}")


tab_exp, tab_chem, tab_mat, tab_expert = st.tabs(["🧾 Experiments", "⚗️ Chemistry", "📦 Materials", "💬 Ask the Signals expert"])

# ------------------------------------------------------------------ experiments
with tab_exp:
    try:
        exps = sc.list_notebook_experiments(notebook["eid"]) if notebook else sc.list_experiments(25)
    except SignalsError as e:
        st.error(e); exps = []
    st.caption(f"Experiments in **{notebook['name']}**" if notebook
               else "Most recently modified experiments you can see. Choose a notebook in the sidebar to narrow this.")
    if exps:
        pick = st.selectbox("Experiment", exps, format_func=lambda x: f"{x['name']}  ·  {x['modifiedAt'][:10]}")
        with st.spinner("Reading the experiment…"):
            try:
                ctx = experiment_context(sc, pick["eid"])
            except SignalsError as e:
                st.error(e); ctx = {"text": "", "sources": []}
        with st.expander(f"What the AI will read ({len(ctx['sources'])} records, {len(ctx['text']):,} chars)"):
            st.code(ctx["text"] or "(empty)", language="markdown")
        q = st.text_area("Ask about this experiment", "Summarise this experiment and flag anything that looks incomplete or inconsistent.")
        if st.button("Ask", key="ask_exp"):
            with st.spinner("Thinking…"):
                show_answer(ai.ask(q, records=ctx["text"]))
    with st.expander("➕ Create an experiment in your notebook"):
        if not notebook:
            st.info("Choose your notebook in the sidebar first.")
        else:
            name = st.text_input("Name", "Hackathon test experiment")
            if st.button("Create"):
                try:
                    new = sc.create_experiment(name, notebook["eid"], "Created from the hackathon starter")
                    st.success(f"Created {new.get('id')} in {notebook['name']}")
                except SignalsError as e:
                    st.error(e)

# ------------------------------------------------------------------ chemistry
with tab_chem:
    left, right = st.columns([1, 2])
    with left:
        mode = st.radio("Find structures", ["Recent drawings", "Substructure search"], horizontal=True)
        if mode == "Recent drawings":
            try:
                items = sc.list_chemical_drawings(15)
            except SignalsError as e:
                st.error(e); items = []
            items = [d for d in items if d.get("smiles")]
            pick = st.selectbox("Drawing", items, format_func=lambda d: d["name"]) if items else None
            eid, smiles, name = (pick["id"], pick["smiles"], pick["name"]) if pick else (None, None, None)
        else:
            query = st.text_input("SMILES (substructure)", "c1ccccc1C(=O)O")
            exact = st.checkbox("Exact match")
            hits = []
            if st.button("Search"):
                try:
                    hits = sc.chemistry_search(query, exact=exact, limit=20)
                    st.session_state["hits"] = hits
                except SignalsError as e:
                    st.error(e)
            hits = st.session_state.get("hits", [])
            st.caption(f"{len(hits)} hits")
            pick = st.selectbox("Hit", hits, format_func=lambda h: f"{h['attributes'].get('name')} ({h['attributes'].get('type')})") if hits else None
            eid, name = (pick["id"], pick["attributes"].get("name")) if pick else (None, None)
            smiles = None
            if pick and pick["attributes"].get("type") == "chemicalDrawing":
                try:
                    smiles = sc.export_entity(eid, "smiles").strip()
                except SignalsError:
                    smiles = None
    with right:
        if eid:
            try:
                svg = sc.get_chemical_drawing(eid, "svg")
                svg = svg[svg.find("<svg"):] if "<svg" in svg else svg      # drop <?xml ...?> / <!DOCTYPE>
                st.markdown(f'<div style="background:#fff;border-radius:8px;padding:8px;max-height:420px;overflow:auto">{svg}</div>',
                            unsafe_allow_html=True)
            except Exception as e:  # noqa: BLE001
                st.caption(f"(no depiction: {e})")
        if smiles:
            info = structure_context(smiles, name)
            st.code(info)
            q = st.text_input("Ask about this structure", "What functional groups are present, and what are its likely liabilities?")
            if st.button("Ask", key="ask_chem"):
                with st.spinner("Thinking…"):
                    show_answer(ai.ask(q, records=info))

# ------------------------------------------------------------------ materials
with tab_mat:
    c1, c2 = st.columns([2, 1])
    with c1:
        mq = st.text_input("Search registered materials (full text, * wildcard)", "")
        try:
            rows = sc.search_materials(mq, 25)
            st.dataframe([{"id": r.get("id"), "name": r.get("attributes", {}).get("name", r.get("name")),
                           **{k: ", ".join(map(str, v)) if isinstance(v, list) else v   # some tags are lists
                              for k, v in (r.get("attributes", {}).get("tags") or {}).items() if k.startswith("materials.")}}
                          for r in rows], width="stretch")
        except SignalsError as e:
            st.error(e)
    with c2:
        try:
            st.write("**Material libraries**")
            st.write([l.get("attributes", {}).get("name", l.get("id")) for l in sc.list_material_libraries()])
        except SignalsError as e:
            st.error(e)

# ------------------------------------------------------------------ Signals expert (knowledge)
with tab_expert:
    st.write("Ask about the Signals REST API, Data Factory API, External Actions / Data Sources / notifications, or how to build an integration. "
             "Answers come from the verified knowledge pack in `docs/signals/`.")
    q = st.text_area("Question", "A customer's search for experiment 'QC-2026-001' returns 40 results. Why, and what's the fix?")
    if st.button("Ask the expert"):
        with st.spinner("Searching the knowledge pack…"):
            kb = knowledge_block(q, k=5)
            show_answer(ai.ask(q, knowledge=kb))
        with st.expander("Knowledge used"):
            for c in search_knowledge(q, 5):
                st.markdown(f"**{c['source']} › {c['heading']}** (score {c['score']})")
            eps = find_endpoints(q)
            if eps:
                st.markdown("**Endpoint index matches**\n\n" + "\n".join(f"- {e}" for e in eps))
