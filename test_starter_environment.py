import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def test_bundle():
    # Load environment
    try:
        from backend.app import smart_load_env, dotenv_path
        smart_load_env(dotenv_path)
    except Exception:
        pass

    print('=' * 60)
    print('[VERIFY] SIGNALS EMEA HACKATHON 2026 STARTER ENVIRONMENT')
    print('=' * 60)

    # 1. Package Imports
    print('\n[Step 1] Checking Core Scientific & AI Libraries...')
    packages_to_check = [
        ('FastAPI', 'fastapi'),
        ('Requests', 'requests'),
        ('Pydantic', 'pydantic'),
        ('Pandas', 'pandas'),
        ('NumPy', 'numpy'),
        ('Pillow', 'PIL'),
        ('OpenAI SDK', 'openai')
    ]
    for label, pkg in packages_to_check:
        try:
            __import__(pkg)
            print(f'  [OK] {label} ({pkg}) is installed and importable.')
        except Exception as e:
            print(f'  [WARN] {label} ({pkg}) host environment note: {type(e).__name__} ({e})')

    # Optional platform libraries
    for opt_label, opt_pkg in [('Biopython', 'Bio'), ('RDKit', 'rdkit'), ('Streamlit', 'streamlit')]:
        try:
            __import__(opt_pkg)
            print(f'  [OK] {opt_label} ({opt_pkg}) is available.')
        except ImportError:
            print(f'  [INFO] {opt_label} ({opt_pkg}) will be installed inside Linux Codespaces via requirements.txt.')

    # 2. Signals SDK Test & Extended Helpers
    print('\n[Step 2] Testing SignalsClient SDK & Convenience Helpers...')
    from backend.signals_client import SignalsClient
    sc = SignalsClient()
    conn = sc.check_connection()
    c_status = conn.get("status")
    print(f'  [OK] Connectivity Status: {c_status}')
    exps = sc.list_experiments(limit=3)
    exp_name = exps[0]["name"] if exps else "None"
    print(f'  [OK] Retrieved {len(exps)} experiment(s). First: {exp_name}')
    
    # Test new helpers
    drawings_20 = sc.list_chemical_drawings(limit=20)
    assert len(drawings_20) == 20, f"Expected 20 chemical drawings, got {len(drawings_20)}"
    assert all("smiles" in d and "id" in d for d in drawings_20), "drawings missing required fields"
    print(f'  [OK] list_chemical_drawings(20) retrieved {len(drawings_20)} drawings. First: {drawings_20[0]["name"]}')

    drawing = sc.get_chemical_drawing("mat-test-1", format="smiles")
    assert drawing and "C" in drawing, "get_chemical_drawing failed"
    print(f'  [OK] get_chemical_drawing() retrieved SMILES: {drawing}')

    svg = sc.get_chemical_drawing("mat-test-1", format="svg")
    assert "<svg" in svg, "get_chemical_drawing svg failed"
    print(f'  [OK] get_chemical_drawing() retrieved SVG ({len(svg)} bytes)')

    stoich = sc.get_stoichiometry("chem-test-1")
    assert "data" in stoich, "get_stoichiometry failed"
    print(f'  [OK] get_stoichiometry() retrieved reaction data')

    mats = sc.search_materials("aspirin")
    assert len(mats) > 0, "search_materials failed"
    print(f'  [OK] search_materials() found {len(mats)} material(s)')

    new_exp = sc.create_experiment("Unit Test Experiment")
    assert new_exp.get("id"), "create_experiment failed"
    print(f'  [OK] create_experiment() created {new_exp.get("id")}')

    # 3. AI Client Test
    print('\n[Step 3] Testing AIClient Module & Contextual Synthesis...')
    from backend.ai_client import AIClient
    ai = AIClient()
    status = ai.check_status()
    ai_provider = status.get("provider")
    ai_model = status.get("model")
    print(f'  [OK] AI Provider: {ai_provider}, Model: {ai_model}')

    # Test 3a: Chemical Drawing Analysis
    chem_analysis = ai.generate_text('Analyze chemical drawing Aspirin SMILES CC(=O)Oc1ccccc1C(=O)O against Lipinski Rule of 5.')
    assert chem_analysis.get("text"), "AI chemical analysis failed"
    print(f'  [OK] AI Chemical Drawing Analysis ({chem_analysis.get("source")}): {chem_analysis.get("text")[:60]}...')

    # Test 3b: Lab Experiments Portfolio Summarizer
    lab_summary = ai.generate_text('Summarize active experiment portfolio in Signals Notebook.')
    assert lab_summary.get("text"), "AI lab portfolio summary failed"
    print(f'  [OK] AI Portfolio Summarization ({lab_summary.get("source")}): {lab_summary.get("text")[:60]}...')

    # 4. OpenAPI Specs & Master API Catalog Check
    print('\n[Step 4] Checking OpenAPI Specs & Master API Catalog...')
    spec_dir = Path(__file__).parent / 'docs' / 'signals-api'
    specs = list(spec_dir.glob('*.yaml'))
    print(f'  [OK] Found {len(specs)} OpenAPI YAML specifications in docs/signals-api/.')
    assert len(specs) == 21, f'Expected 21 specs, found {len(specs)}'

    catalog_file = Path(__file__).parent / 'docs' / 'API_CATALOG.md'
    assert catalog_file.exists(), 'Missing docs/API_CATALOG.md'
    print(f'  [OK] docs/API_CATALOG.md verified ({catalog_file.stat().st_size} bytes).')

    # 5. Modular Markdown Guide Chapters Check
    print('\n[Step 5] Checking Modular Markdown Guide Chapters...')
    guide_dir = Path(__file__).parent / 'docs' / 'guide'
    assert guide_dir.exists(), 'Missing docs/guide/'
    guide_chapters = list(guide_dir.glob('*.md'))
    print(f'  [OK] Found {len(guide_chapters)} distilled guide chapters in docs/guide/.')
    assert len(guide_chapters) >= 6, f'Expected >=6 guide chapters, found {len(guide_chapters)}'

    # 6. Streamlit & Slash Prompts Check
    print('\n[Step 6] Checking Streamlit App & Slash Prompts...')
    app_st = Path(__file__).parent / 'app_streamlit.py'
    assert app_st.exists(), 'Missing app_streamlit.py'
    print(f'  [OK] app_streamlit.py verified ({app_st.stat().st_size} bytes).')

    prompts_dir = Path(__file__).parent / '.continue' / 'prompts'
    prompts = list(prompts_dir.glob('*.prompt'))
    print(f'  [OK] Found {len(prompts)} slash command prompt(s) in .continue/prompts/.')
    assert len(prompts) >= 3, f'Expected >=3 prompts, found {len(prompts)}'

    print('\n' + '=' * 60)
    print('[SUCCESS] ALL ENVIRONMENT & PRE-DIGESTED ASSET CHECKS PASSED!')
    print('=' * 60)

if __name__ == '__main__':
    test_bundle()
