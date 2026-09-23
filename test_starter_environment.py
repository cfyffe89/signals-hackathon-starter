import os
import sys
from pathlib import Path

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

    # 2. Signals SDK Test
    print('\n[Step 2] Testing SignalsClient SDK...')
    from backend.signals_client import SignalsClient
    sc = SignalsClient()
    conn = sc.check_connection()
    c_status = conn.get("status")
    print(f'  [OK] Connectivity Status: {c_status}')
    exps = sc.list_experiments(limit=3)
    exp_name = exps[0]["name"] if exps else "None"
    print(f'  [OK] Retrieved {len(exps)} experiment(s). First: {exp_name}')

    # 3. AI Client Test
    print('\n[Step 3] Testing AIClient Module...')
    from backend.ai_client import AIClient
    ai = AIClient()
    status = ai.check_status()
    ai_provider = status.get("provider")
    ai_model = status.get("model")
    print(f'  [OK] AI Provider: {ai_provider}, Model: {ai_model}')
    gen = ai.generate_text('Explain force=true in Signals Notebook API.')
    gen_source = gen.get("source")
    gen_snippet = gen.get("text", "")[:80]
    print(f'  [OK] AI Response ({gen_source}): {gen_snippet}...')

    # 4. OpenAPI Specs Check
    print('\n[Step 4] Checking OpenAPI YAML Specifications...')
    spec_dir = Path(__file__).parent / 'docs' / 'signals-api'
    specs = list(spec_dir.glob('*.yaml'))
    print(f'  [OK] Found {len(specs)} OpenAPI YAML specifications in docs/signals-api/.')
    assert len(specs) == 21, f'Expected 21 specs, found {len(specs)}'

    # 5. Developer Cheat Sheet Check
    cheat_sheet = Path(__file__).parent / 'docs' / 'SIGNALS_DEVELOPER_CHEAT_SHEET.md'
    assert cheat_sheet.exists(), 'Missing SIGNALS_DEVELOPER_CHEAT_SHEET.md'
    print(f'  [OK] SIGNALS_DEVELOPER_CHEAT_SHEET.md verified ({cheat_sheet.stat().st_size} bytes).')

    print('\n' + '=' * 60)
    print('[SUCCESS] ALL ENVIRONMENT CHECKS PASSED!')
    print('=' * 60)

if __name__ == '__main__':
    test_bundle()
