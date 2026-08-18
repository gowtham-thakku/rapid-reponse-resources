// Renders an extracted spreadsheet grid (see extract_sheet.py) as an editable,
// live-recalculating HTML table backed by HyperFormula. Input cells are
// auto-detected: any cell containing the literal text "X =" marks the cell
// immediately to its right as an editable number input.

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function formatValue(v) {
  if (typeof v === "number") {
    const rounded = Math.round(v * 100) / 100;
    return String(rounded);
  }
  if (v === null || v === undefined) return "";
  return String(v);
}

function buildArray(sheetData) {
  const arr = [];
  for (let r = 0; r < sheetData.maxRow; r++) {
    const row = [];
    for (let c = 0; c < sheetData.maxCol; c++) {
      const cell = sheetData.cells[`${r},${c}`];
      if (!cell) { row.push(null); continue; }
      row.push(cell.f !== undefined ? cell.f : cell.v);
    }
    arr.push(row);
  }
  return arr;
}

function findMerge(merges, r, c) {
  for (const m of merges) {
    if (r >= m.r1 && r <= m.r2 && c >= m.c1 && c <= m.c2) return m;
  }
  return null;
}

async function renderCalcSheet(containerId, dataUrl) {
  const container = document.getElementById(containerId);
  const res = await fetch(dataUrl);
  const sheetData = await res.json();

  const inputCoords = new Set();
  for (const [key, cell] of Object.entries(sheetData.cells)) {
    if (cell.v === "X =") {
      const [r, c] = key.split(",").map(Number);
      inputCoords.add(`${r},${c + 1}`);
    }
  }

  const array = buildArray(sheetData);
  const hf = HyperFormula.buildFromArray(array, { licenseKey: "gpl-v3" });

  const table = document.createElement("table");
  table.className = "calc-sheet";
  const formulaCells = [];
  const skip = new Set();

  for (let r = 0; r < sheetData.maxRow; r++) {
    const tr = document.createElement("tr");
    for (let c = 0; c < sheetData.maxCol; c++) {
      if (skip.has(`${r},${c}`)) continue;
      const merge = findMerge(sheetData.merges, r, c);
      let colspan = 1, rowspan = 1;
      if (merge) {
        if (merge.r1 !== r || merge.c1 !== c) continue;
        colspan = merge.c2 - merge.c1 + 1;
        rowspan = merge.r2 - merge.r1 + 1;
        for (let mr = merge.r1; mr <= merge.r2; mr++) {
          for (let mc = merge.c1; mc <= merge.c2; mc++) {
            if (mr !== r || mc !== c) skip.add(`${mr},${mc}`);
          }
        }
      }

      const td = document.createElement("td");
      if (colspan > 1) td.colSpan = colspan;
      if (rowspan > 1) td.rowSpan = rowspan;

      const key = `${r},${c}`;
      const cell = sheetData.cells[key];
      if (cell) {
        if (cell.bold) td.style.fontWeight = "600";
        if (cell.fill) td.style.background = cell.fill;

        if (inputCoords.has(key)) {
          const input = document.createElement("input");
          input.type = "number";
          input.step = "any";
          input.className = "calc-input";
          input.value = cell.v;
          input.addEventListener("input", () => {
            const num = parseFloat(input.value);
            hf.setCellContents({ sheet: 0, row: r, col: c }, isNaN(num) ? 0 : num);
            formulaCells.forEach(({ row, col, el }) => {
              el.textContent = formatValue(hf.getCellValue({ sheet: 0, row, col }));
            });
          });
          td.appendChild(input);
        } else if (cell.f !== undefined) {
          const span = document.createElement("span");
          span.textContent = formatValue(hf.getCellValue({ sheet: 0, row: r, col: c }));
          td.appendChild(span);
          formulaCells.push({ row: r, col: c, el: span });
        } else {
          td.innerHTML = escapeHtml(cell.v).replace(/\n/g, "<br>");
        }
      }
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }

  container.appendChild(table);
}
