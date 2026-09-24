"""Turn Signals records into compact text an LLM can reason over.

GET /entities/{eid}/export returns text elements as HTML and tables (grid, materialsTable,
samplesContainer) as CSV; chemical drawings export as SMILES. Worksheets export empty.
"""
import html
import re
from typing import Optional

from .signals_client import SignalsClient

EXPORTABLE = {"text", "grid", "materialsTable", "samplesContainer", "chemicalDrawing"}


def _strip_html(s: str) -> str:
    s = re.sub(r"(?is)<(script|style).*?</\1>", "", s)
    s = re.sub(r"(?i)</(p|h\d|li|tr|div)>|<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</t[dh]>", " | ", s)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(s)).strip()


def experiment_context(sc: SignalsClient, eid: str, max_chars: int = 12000, per_item: int = 2500) -> dict:
    """
    Read an experiment (or any container entity) and its children into text.
    Returns {"text": ..., "sources": [{"eid", "type", "name"}]} so answers can cite what was used.
    """
    ent = sc.get_entity(eid)
    a = ent.get("attributes", {})
    lines = [f"# {a.get('name', eid)}  ({a.get('type', eid.split(':')[0])}, {eid})"]
    if a.get("description"):
        lines.append(f"Description: {a['description']}")
    for k in ("createdAt", "modifiedAt", "state"):
        if a.get(k):
            lines.append(f"{k}: {a[k]}")
    fields = a.get("fields") or {}
    for name, f in list(fields.items())[:25]:
        val = f.get("value") if isinstance(f, dict) else f
        if val not in (None, "", []):
            lines.append(f"{name}: {val}")
    sources = [{"eid": eid, "type": a.get("type"), "name": a.get("name")}]
    used = sum(len(l) for l in lines)
    for child in sc.list_child_entities(eid):
        ca = child.get("attributes", {})
        ctype, cname, ceid = ca.get("type") or child.get("type"), ca.get("name", ""), child.get("id")
        if used > max_chars:
            lines.append(f"... (more children not included: context limit)")
            break
        body = ""
        if ctype in EXPORTABLE and not sc.mock_mode:
            try:
                raw = sc.export_entity(ceid, "smiles") if ctype == "chemicalDrawing" else sc.export_entity(ceid, "")
                body = _strip_html(raw) if ctype == "text" else raw.strip()
            except Exception as e:  # keep going; say what could not be read
                body = f"(could not export: {str(e)[:80]})"
        elif sc.mock_mode:
            body = "(mock mode: no content)"
        label = "SMILES" if ctype == "chemicalDrawing" else ("CSV" if ctype in ("grid", "materialsTable", "samplesContainer") else "")
        block = f"\n## {ctype}: {cname}" + (f" [{label}]" if label else "") + (f"\n{body[:per_item]}" if body else "")
        lines.append(block)
        used += len(block)
        sources.append({"eid": ceid, "type": ctype, "name": cname})
    return {"text": "\n".join(lines)[:max_chars], "sources": sources}


def _describe(m) -> str:
    from rdkit.Chem import Descriptors, Crippen, Lipinski, rdMolDescriptors
    return (f"{rdMolDescriptors.CalcMolFormula(m)}, MW {Descriptors.MolWt(m):.2f}, cLogP {Crippen.MolLogP(m):.2f}, "
            f"TPSA {rdMolDescriptors.CalcTPSA(m):.1f}, HBD {Lipinski.NumHDonors(m)}, HBA {Lipinski.NumHAcceptors(m)}, "
            f"RotB {Lipinski.NumRotatableBonds(m)}")


def structure_context(smiles: str, name: Optional[str] = None) -> str:
    """RDKit descriptors for a SMILES. Reaction SMILES (reactants>>products) are split into their components."""
    smiles = smiles.strip().split()[0] if smiles.strip() else ""
    out = [f"Structure{f' ({name})' if name else ''}: {smiles}"]
    try:
        from rdkit import Chem
    except ImportError:
        return chr(10).join(out + ["(RDKit not installed: descriptors unavailable)"])
    if ">" in smiles:
        parts = smiles.split(">")
        roles = {"reactants": parts[0], "agents": parts[1] if len(parts) == 3 else "", "products": parts[-1]}
        out.append("Reaction:")
        for role, sub in roles.items():
            for frag in [f for f in sub.split(".") if f]:
                m = Chem.MolFromSmiles(frag)
                out.append(f"  {role[:-1]}: {frag}  ->  {_describe(m) if m else '(unparseable)'}")
    else:
        m = Chem.MolFromSmiles(smiles)
        out.append(_describe(m) if m else "(RDKit could not parse this SMILES)")
        if m and len(Chem.GetMolFrags(m)) > 1:
            out.append(f"{len(Chem.GetMolFrags(m))} disconnected fragments (mixture or salt)")
    return chr(10).join(out)
