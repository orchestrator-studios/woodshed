"""Render prose-shaped spreadsheet tabs as faithful Markdown.

Part of the intake skill (stage 4 - derive). For workbooks that embed
operating documents - column dictionaries, process guides, how-to tabs -
this extracts named tabs into one readable .md. Data tabs get measured,
not converted; this is for the prose ones.

Usage:
    python xlsx_tabs_to_md.py WORKBOOK.xlsx -t "Tab One" -t "Tab Two" -o out.md
        [--title "Document title"] [--note "extra header line"]

Heuristic: a row with one populated cell becomes a heading (short, no
terminal period) or a paragraph; consecutive rows with 2+ populated cells
become a table, first row as its header. Newlines inside cells collapse to
spaces; pipes are escaped. The output header records the exact command that
regenerates it - raw always wins over derived.
"""
import argparse
import re
import sys

import openpyxl


def clean(v):
    s = str(v).replace("\n", " ").strip()
    return re.sub(r"\s{2,}", " ", s).replace("|", "\\|")


def tab_to_md(ws):
    lines = []
    table = []

    def flush():
        nonlocal table
        if not table:
            return
        width = max(len(r) for r in table)
        rows = [r + [""] * (width - len(r)) for r in table]
        lines.append("| " + " | ".join(rows[0]) + " |")
        lines.append("|" + "---|" * width)
        for r in rows[1:]:
            lines.append("| " + " | ".join(r) + " |")
        lines.append("")
        table = []

    for row in ws.iter_rows():
        cells = [clean(c.value) for c in row if c.value not in (None, "")]
        if not cells:
            continue
        if len(cells) == 1:
            flush()
            text = cells[0]
            if len(text) <= 90 and not text.endswith("."):
                lines.append(f"### {text}\n")
            else:
                lines.append(f"{text}\n")
        else:
            table.append(cells)
    flush()
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("workbook")
    ap.add_argument("-t", "--tab", action="append", required=True, dest="tabs")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--title")
    ap.add_argument("--note", action="append", default=[])
    args = ap.parse_args()

    wb = openpyxl.load_workbook(args.workbook, data_only=True)
    missing = [t for t in args.tabs if t not in wb.sheetnames]
    if missing:
        sys.exit(f"tabs not found: {missing}; workbook has {wb.sheetnames}")

    cmd = "python xlsx_tabs_to_md.py " + " ".join(
        [args.workbook] + [f'-t "{t}"' for t in args.tabs] + [f"-o {args.out}"]
    )
    title = args.title or f"{args.workbook} — extracted tabs (derived)"
    out = [f"# {title}", ""]
    out.append(f"Faithful Markdown rendering of {len(args.tabs)} tab(s) in `{args.workbook}`.")
    out.append("Derived and regenerable — the workbook is the source of truth. Regenerate with:")
    out.append(f"`{cmd}` (script: intake skill, `scripts/xlsx_tabs_to_md.py`).")
    out.extend(args.note)
    out.append("")
    for t in args.tabs:
        out.append(f"\n## Tab: {t}\n")
        out.extend(tab_to_md(wb[t]))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
