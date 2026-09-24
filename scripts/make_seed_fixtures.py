"""Generate the synthetic seed fixtures in seed/fixtures/ (organiser-only; the outputs are committed).

    pip install pymupdf
    python scripts/make_seed_fixtures.py

Writes: LCMS and NMR PDF reports (vendor-style, for the PDF-parser use case), an HPLC results CSV
(closing-the-loop use case) and a 100-line incoming shipment manifest (bulk registration use case).
Every file is marked SYNTHETIC DEMO DATA. Deterministic (fixed random seed).
"""
import csv
import math
import random
from pathlib import Path

import pymupdf

OUT = Path(__file__).resolve().parents[1] / "seed" / "fixtures"
MARK = "SYNTHETIC DEMO DATA - Signals EMEA Hackathon 2026"
random.seed(2026)


def _header(page, title, meta):
    page.insert_text((50, 50), title, fontsize=15, fontname="hebo")
    page.insert_text((50, 66), MARK, fontsize=8, color=(0.6, 0, 0))
    y = 90
    for k, v in meta:
        page.insert_text((50, y), f"{k}:", fontsize=9, fontname="hebo")
        page.insert_text((175, y), v, fontsize=9)
        y += 13
    return y + 8


def _table(page, y, cols, widths, rows):
    x0 = 50
    for i, c in enumerate(cols):
        page.insert_text((x0 + sum(widths[:i]), y), c, fontsize=8.5, fontname="hebo")
    page.draw_line((x0, y + 4), (x0 + sum(widths), y + 4), width=0.5)
    y += 16
    for r in rows:
        for i, v in enumerate(r):
            page.insert_text((x0 + sum(widths[:i]), y), str(v), fontsize=8.5)
        y += 13
    return y + 10


def _trace(page, rect, xs, ys, xlabel, invert_x=False):
    x0, y0, x1, y1 = rect
    page.draw_rect(pymupdf.Rect(rect), width=0.5)
    xmin, xmax, ymax = min(xs), max(xs), max(ys) * 1.1
    def px(x):
        f = (x - xmin) / (xmax - xmin)
        return x1 - f * (x1 - x0) if invert_x else x0 + f * (x1 - x0)
    pts = [(px(x), y1 - (y / ymax) * (y1 - y0)) for x, y in zip(xs, ys)]
    page.draw_polyline(pts, width=0.6, color=(0, 0, 0.7))
    for i in range(6):
        v = xmin + i * (xmax - xmin) / 5
        page.insert_text((px(v) - 8, y1 + 11), f"{v:.1f}", fontsize=7)
    page.insert_text(((x0 + x1) / 2 - 20, y1 + 23), xlabel, fontsize=8)


def lcms_pdf():
    peaks = [  # rt, area %, name, m/z
        (1.95, 0.2, "Unknown", "154.1"),
        (2.41, 0.4, "4-Bromobenzonitrile", "182.0 / 184.0"),
        (2.87, 99.1, "4-Cyanobiphenyl", "180.1 [M+H]+"),
        (3.35, 0.3, "Biphenyl (homocoupling)", "155.1"),
    ]
    doc = pymupdf.open()
    p = doc.new_page()
    y = _header(p, "LC-MS Analysis Report", [
        ("Sample", "26-S1-001  4-cyanobiphenyl (crude recryst.)"), ("ELN reference", "Step 1: Suzuki coupling to 4-cyanobiphenyl"),
        ("Project", "HACK-SYN-01"), ("Analyst", "A. Analyst"), ("Acquired", "2026-10-14 10:42:17"),
        ("Instrument", "UHPLC-MS system 3 (single quadrupole, ESI+)"), ("Method", "GEN_5-95_3MIN.m"),
        ("Column", "C18, 2.1 x 50 mm, 1.7 um, 40 C"), ("Mobile phase", "A: water + 0.1% formic acid; B: acetonitrile + 0.1% formic acid"),
        ("Gradient", "5-95% B in 3.0 min, 0.6 mL/min"), ("Detection", "UV 254 nm; MS scan m/z 100-800"),
    ])
    xs = [i * 0.005 for i in range(801)]
    ys = [0.3 + sum(a * math.exp(-((x - rt) ** 2) / (2 * 0.018 ** 2)) for rt, a, *_ in peaks) for x in xs]
    _trace(p, (50, y, 545, y + 170), xs, ys, "Retention time (min), UV 254 nm")
    y += 205
    total = sum(a for _, a, *_ in peaks)
    rows = [(i + 1, f"{rt:.2f}", f"{a * 12500:,.0f}", f"{a / total * 100:.1f}", name, mz) for i, (rt, a, name, mz) in enumerate(peaks)]
    y = _table(p, y, ["Peak", "RT (min)", "Area", "Area %", "Name", "m/z"], [35, 55, 70, 50, 150, 100], rows)
    p.insert_text((50, y), "Purity (UV 254 nm, area %): 99.1%.   Main peak identity confirmed by MS.", fontsize=9)
    doc.save(OUT / "LCMS_report_4-cyanobiphenyl.pdf")


def nmr_pdf():
    shifts = [(7.74, 2, "d", "8.4"), (7.69, 2, "d", "8.4"), (7.59, 2, "d", "7.3"), (7.49, 2, "t", "7.5"), (7.43, 1, "t", "7.3")]
    doc = pymupdf.open()
    p = doc.new_page()
    y = _header(p, "1H NMR Report", [
        ("Sample", "26-S1-001  4-cyanobiphenyl"), ("ELN reference", "Analytical results: 4-cyanobiphenyl lot 26-S1-001"),
        ("Structure (SMILES)", "N#Cc1ccc(-c2ccccc2)cc1"), ("Formula / MW", "C13H9N / 179.22"),
        ("Operator", "N. Spectroscopist"), ("Acquired", "2026-10-14 14:05:51"), ("Spectrometer", "400 MHz"),
        ("Nucleus", "1H"), ("Solvent", "CDCl3"), ("Temperature", "298 K"), ("Scans", "16"), ("Pulse program", "zg30"),
    ])
    xs = [6.8 + i * 0.001 for i in range(1401)]
    lines = []
    for d, n, m, j in shifts:
        split = [-0.5, 0.5] if m == "d" else [-1, 0, 1]
        wts = [1, 1] if m == "d" else [1, 2, 1]
        for s, w in zip(split, wts):
            lines.append((d + s * float(j) / 400, n * w / sum(wts)))
    lines.append((7.26, 0.25))  # residual CHCl3
    ys = [0.01 + sum(h / (1 + ((x - c) / 0.0015) ** 2) for c, h in lines) for x in xs]
    _trace(p, (50, y, 545, y + 170), xs, ys, "Chemical shift (ppm)", invert_x=True)
    y += 205
    rows = [(f"{d:.2f}", m, j, n, "ArH") for d, n, m, j in shifts]
    y = _table(p, y, ["delta (ppm)", "Mult.", "J (Hz)", "Integral (H)", "Assignment"], [70, 45, 55, 75, 100], rows)
    p.insert_text((50, y), "13C NMR (101 MHz, CDCl3): delta 145.7, 139.2, 132.6, 129.1, 128.7, 127.7, 127.2, 119.0, 110.9.", fontsize=9)
    p.insert_text((50, y + 14), "Conclusion: consistent with the proposed structure.", fontsize=9)
    doc.save(OUT / "NMR_report_4-cyanobiphenyl.pdf")


def hplc_csv():
    with open(OUT / "hplc_results_F-101.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["# " + MARK])
        w.writerow(["Sample", "Lot", "Replicate", "Assay (% label claim)", "Largest impurity (%)", "Total impurities (%)", "Injected", "Result"])
        w.writerow(["F-101", "26-0917", 1, 99.4, 0.08, 0.21, "2026-10-19T10:12:00Z", "PASS"])
        w.writerow(["F-101", "26-0917", 2, 99.8, 0.07, 0.19, "2026-10-19T10:31:00Z", "PASS"])


REAGENTS = [  # name, CAS, SMILES, unit, pack sizes
    ("Toluene", "108-88-3", "Cc1ccccc1", "mL", [1000, 2500]), ("Tetrahydrofuran", "109-99-9", "C1CCOC1", "mL", [500, 1000]),
    ("Methanol", "67-56-1", "CO", "mL", [1000, 2500]), ("Ethanol", "64-17-5", "CCO", "mL", [1000]),
    ("Acetone", "67-64-1", "CC(C)=O", "mL", [1000, 2500]), ("Acetonitrile", "75-05-8", "CC#N", "mL", [1000, 2500]),
    ("Dichloromethane", "75-09-2", "ClCCl", "mL", [1000]), ("Dimethyl sulfoxide", "67-68-5", "CS(C)=O", "mL", [250, 500]),
    ("N,N-Dimethylformamide", "68-12-2", "CN(C)C=O", "mL", [1000]), ("Ethyl acetate", "141-78-6", "CCOC(C)=O", "mL", [1000, 2500]),
    ("Diethyl ether", "60-29-7", "CCOCC", "mL", [500]), ("n-Hexane", "110-54-3", "CCCCCC", "mL", [1000]),
    ("2-Propanol", "67-63-0", "CC(C)O", "mL", [1000]), ("Acetic acid", "64-19-7", "CC(O)=O", "mL", [500]),
    ("Triethylamine", "121-44-8", "CCN(CC)CC", "mL", [250]), ("Sodium hydroxide", "1310-73-2", "[Na+].[OH-]", "g", [500, 1000]),
    ("Sodium chloride", "7647-14-5", "[Na+].[Cl-]", "g", [1000]), ("Potassium carbonate", "584-08-7", "[K+].[K+].[O-]C([O-])=O", "g", [500]),
    ("Sodium bicarbonate", "144-55-8", "[Na+].OC([O-])=O", "g", [500, 1000]), ("Magnesium sulfate", "7487-88-9", "[Mg+2].[O-]S([O-])(=O)=O", "g", [500]),
    ("Sodium sulfate", "7757-82-6", "[Na+].[Na+].[O-]S([O-])(=O)=O", "g", [500]), ("Phenylboronic acid", "98-80-6", "OB(O)c1ccccc1", "g", [25, 100]),
    ("4-Bromobenzonitrile", "623-00-7", "Brc1ccc(C#N)cc1", "g", [25]), ("Bromobenzene", "108-86-1", "Brc1ccccc1", "mL", [100]),
    ("Benzophenone", "119-61-9", "O=C(c1ccccc1)c1ccccc1", "g", [100]), ("Iodine", "7553-56-2", "II", "g", [100]),
    ("Caffeine", "58-08-2", "Cn1cnc2c1c(=O)n(C)c(=O)n2C", "g", [10, 50]), ("Acetylsalicylic acid", "50-78-2", "CC(=O)Oc1ccccc1C(O)=O", "g", [100]),
    ("Paracetamol", "103-90-2", "CC(=O)Nc1ccc(O)cc1", "g", [100]), ("Benzoic acid", "65-85-0", "OC(=O)c1ccccc1", "g", [100, 500]),
    ("Benzylamine", "100-46-9", "NCc1ccccc1", "mL", [100]),
]


def shipment_csv():
    with open(OUT / "incoming_shipment.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["# " + MARK + ". Supplier names are fictional."])
        w.writerow(["Line", "PO number", "Supplier", "Catalog no", "Name", "CAS", "SMILES", "Lot", "Quantity", "Unit",
                    "Container type", "Received", "Expiry date", "Destination"])
        suppliers = ["Acme Fine Chemicals", "Rhine Lab Supply", "Nordic Reagents"]
        for i in range(100):
            name, cas, smi, unit, sizes = REAGENTS[i % len(REAGENTS)]
            sup = suppliers[i % 3]
            qty = random.choice(sizes)
            ctype = "Bottle" if unit == "mL" else random.choice(["Bottle", "Can"])
            exp = f"20{random.choice([27, 27, 28, 29])}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            w.writerow([i + 1, "PO-2026-10-0412", sup, f"{sup[:2].upper()}-{random.randint(10000, 99999)}", name, cas, smi,
                        f"L{random.randint(100000, 999999)}", qty, unit, ctype, "2026-10-20", exp, "Stockroom"])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    lcms_pdf(); nmr_pdf(); hplc_csv(); shipment_csv()
    print("wrote", sorted(p.name for p in OUT.iterdir()))
