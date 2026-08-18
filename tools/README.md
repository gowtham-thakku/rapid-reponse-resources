# Conversion tooling

Regenerates the hosted `docs/` pages from the original files in `resources/`.

## Setup

- [LibreOffice](https://www.libreoffice.org/) installed, with `soffice` on your PATH (`brew install --cask libreoffice` on macOS)
- `pip install -r tools/requirements.txt`

## Usage

Regenerate everything listed in `resources.json`:

```
python3 tools/convert.py
```

Regenerate just one resource after editing it:

```
python3 tools/convert.py "resources/protocols/Biohub Rapid Response mNGS Protocols Shared.docx"
```

## Adding a new resource

1. Add the source file under the matching `resources/<category>/` folder.
2. Create its `docs/<category>/<slug>/` page (copy an existing one as a template) with a `content.html`, `slides.pdf`, or `sheet-data.json` placeholder — the folder must already exist before converting.
3. Add an entry to `resources.json`:
   - `type: "docx"` or `"xlsx-static"` → converts to `content.html`, embedded via iframe
   - `type: "pptx"` → converts to `slides.pdf`
   - `type: "xlsx-interactive"` → converts to `sheet-data.json` (for the live HyperFormula calculator) plus a `content.html` static fallback; requires a `"sheet"` field naming the worksheet to extract
   - `extraCss` (optional) → CSS injected into the converted `content.html`'s `<style>` block, e.g. to normalize fonts
4. Run `python3 tools/convert.py "resources/<category>/<file>"` and check the page locally before committing.

Hand-authored files (`index.html`, `interactive.html`, `calc-sheet.js`, `style.css`) are never touched by the script — only `content.html`, `slides.pdf`, and `sheet-data.json` are regenerated.
