#!/usr/bin/env python3
"""Regenerates docs/ pages from resources/ source files.

Usage:
    tools/convert.py                                  # regenerate everything in resources.json
    tools/convert.py "resources/protocols/Biohub ...docx"   # regenerate just the matching entry

Requires `soffice` (LibreOffice) on PATH, and openpyxl for xlsx-interactive
entries (pip install openpyxl).
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = Path(__file__).resolve().parent / "resources.json"


def load_manifest():
    with open(MANIFEST_PATH) as f:
        return json.load(f)["entries"]


def soffice_convert(src, out_format, outdir):
    subprocess.run(
        ["soffice", "--headless", "--convert-to", out_format, "--outdir", str(outdir), str(src)],
        check=True, capture_output=True, text=True,
    )
    converted = list(Path(outdir).glob(f"*.{out_format}"))
    if not converted:
        raise RuntimeError(f"soffice produced no .{out_format} file for {src}")
    return converted[0]


def inject_css(html_path, extra_css):
    if not extra_css:
        return
    text = html_path.read_text(encoding="utf-8")
    marker = "<style type=\"text/css\">"
    idx = text.find(marker)
    if idx == -1:
        raise RuntimeError(f"could not find <style> tag to patch in {html_path}")
    insert_at = idx + len(marker)
    text = text[:insert_at] + "\n\t\t" + extra_css + "\n" + text[insert_at:]
    html_path.write_text(text, encoding="utf-8")


def convert_docx_or_xlsx_static(src_path, docs_dir, extra_css):
    with tempfile.TemporaryDirectory() as tmp:
        html_file = soffice_convert(src_path, "html", tmp)
        inject_css(html_file, extra_css)
        shutil.copy(html_file, docs_dir / "content.html")
        # copy any extracted images (e.g. "Name_html_xxxxx.png") alongside
        for asset in Path(tmp).glob("*_html_*"):
            shutil.copy(asset, docs_dir / asset.name)
    print(f"  -> {docs_dir / 'content.html'}")


def convert_pptx(src_path, docs_dir):
    with tempfile.TemporaryDirectory() as tmp:
        pdf_file = soffice_convert(src_path, "pdf", tmp)
        shutil.copy(pdf_file, docs_dir / "slides.pdf")
    print(f"  -> {docs_dir / 'slides.pdf'}")


def convert_xlsx_interactive(src_path, docs_dir, sheet_name):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import extract_sheet

    data = extract_sheet.extract(str(src_path), sheet_name)
    out_path = docs_dir / "sheet-data.json"
    with open(out_path, "w") as f:
        json.dump(data, f, indent=0)
    print(f"  -> {out_path} ({len(data['cells'])} cells, {len(data['merges'])} merges)")
    # also refresh the flattened "static view" tab
    convert_docx_or_xlsx_static(src_path, docs_dir, extra_css=None)


def run_entry(entry):
    src_path = REPO_ROOT / entry["source"]
    docs_dir = REPO_ROOT / entry["docsDir"]
    if not src_path.exists():
        raise FileNotFoundError(f"source not found: {src_path}")
    if not docs_dir.exists():
        raise FileNotFoundError(f"docs dir not found: {docs_dir}")

    print(f"Converting {entry['source']} ({entry['type']})")
    if entry["type"] == "docx":
        convert_docx_or_xlsx_static(src_path, docs_dir, entry.get("extraCss"))
    elif entry["type"] == "pptx":
        convert_pptx(src_path, docs_dir)
    elif entry["type"] == "xlsx-static":
        convert_docx_or_xlsx_static(src_path, docs_dir, entry.get("extraCss"))
    elif entry["type"] == "xlsx-interactive":
        convert_xlsx_interactive(src_path, docs_dir, entry["sheet"])
    else:
        raise ValueError(f"unknown type: {entry['type']}")


def main():
    entries = load_manifest()
    target = sys.argv[1] if len(sys.argv) > 1 else None

    if target:
        matches = [e for e in entries if e["source"] == target or str(REPO_ROOT / e["source"]) == target]
        if not matches:
            print(f"No manifest entry for: {target}", file=sys.stderr)
            print("Known sources:", file=sys.stderr)
            for e in entries:
                print(f"  {e['source']}", file=sys.stderr)
            sys.exit(1)
        entries = matches

    for entry in entries:
        run_entry(entry)


if __name__ == "__main__":
    main()
