/**
 * Capita Score — helpers (no external libs)
 * - CSV parser (handles quoted fields)
 * - Table renderer w/ sorting + search
 */

export function $(sel, root=document){ return root.querySelector(sel); }
export function $all(sel, root=document){ return [...root.querySelectorAll(sel)]; }

export function formatNumber(v, {decimals=1, suffix=""}={}){
  if (v === null || v === undefined || v === "" || Number.isNaN(Number(v))) return "—";
  const n = Number(v);
  return n.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + suffix;
}
export function formatInt(v){
  if (v === null || v === undefined || v === "" || Number.isNaN(Number(v))) return "—";
  return Math.round(Number(v)).toLocaleString();
}
export function formatPercent(v, {decimals=1}={}){
  if (v === null || v === undefined || v === "" || Number.isNaN(Number(v))) return "—";
  return Number(v).toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + "%";
}

export function teamPositionLabel(pos){
  const raw = String(pos ?? "").trim();
  if (!raw) return "—";
  const k = raw.toUpperCase();
  const m = {
    // abreviações
    "TOP":"TOP",
    "JG":"JG",
    "MID":"MID",
    "ADC":"ADC",
    "SUP":"SUP",

    // nomes padrão da Riot / alguns exports
    "JUNGLE":"JG",
    "MIDDLE":"MID",
    "BOTTOM":"ADC",
    "UTILITY":"SUP",

    // sinônimos comuns
    "BOT":"ADC",
    "SUPPORT":"SUP",
  };
  return m[k] || raw;
}

/** Robust-enough CSV parser for small/medium exports */
export function parseCSV(text){
  if (!text) return [];

  // Remove BOM e normaliza quebras de linha
  text = text.replace(/^\uFEFF/, "");
  text = text.replace(/\r\n/g, "\n").replace(/\r/g, "\n");

  // Detecta separador (Metabase costuma usar ',', mas alguns exports locais usam ';')
  const firstLine = (text.split("\n").find(l => l.trim().length) || "");
  const count = (s) => (firstLine.match(new RegExp(`\\${s}`, "g")) || []).length;
  const cComma = count(",");
  const cSemi  = count(";");
  const cTab   = count("\t");
  const sep = (cSemi > cComma && cSemi >= cTab) ? ";" : (cTab > cComma && cTab > cSemi) ? "\t" : ",";

  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;

  for (let i=0;i<text.length;i++){
    const c = text[i];

    if (inQuotes){
      if (c === '"'){
        const next = text[i+1];
        if (next === '"'){
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += c;
      }
      continue;
    }

    if (c === '"'){ inQuotes = true; continue; }

    if (c === sep){
      row.push(field);
      field = "";
      continue;
    }

    if (c === '\n'){
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
      continue;
    }

    field += c;
  }

  // último campo
  if (field.length || row.length){
    row.push(field);
    rows.push(row);
  }

  // remove linhas vazias no fim
  while (rows.length && rows[rows.length-1].every(v => String(v ?? "") === "")) rows.pop();
  if (!rows.length) return [];

  const header = rows[0].map(h => String(h ?? "").trim());
  const out = [];
  for (let r=1;r<rows.length;r++){
    const obj = {};
    for (let c=0;c<header.length;c++){
      const key = header[c];
      let v = String(rows[r][c] ?? "").trim();
      if (v === "NaN") v = "";
      obj[key] = v;
    }
    out.push(obj);
  }
  return out;
}

export async function fetchCSV(url){
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Falha ao carregar CSV (${res.status}) → ${url}`);
  const txt = await res.text();
  return parseCSV(txt);
}

export function setActiveNav(activeKey){
  const links = $all("[data-nav]");
  links.forEach(a => {
    if (a.dataset.nav === activeKey) a.classList.add("active");
  });
}

export function makeSearch(onInput, placeholder="Pesquisar..."){
  const wrap = document.createElement("div");
  wrap.className = "search";
  const input = document.createElement("input");
  input.type = "search";
  input.placeholder = placeholder;
  input.autocomplete = "off";
  input.addEventListener("input", () => onInput(input.value));
  wrap.appendChild(input);
  return {wrap, input};
}

function normalizeText(s){
  return String(s ?? "")
    .normalize("NFD").replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

export function createTable({ columns, rows, initialSortKey=null, initialSortDir="desc", rowIdKey=null }){
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const tbody = document.createElement("tbody");

  let sortKey = initialSortKey || columns.find(c => c.sortable !== false)?.key;
  let sortDir = initialSortDir;

  const renderHead = () => {
    thead.innerHTML = "";
    const tr = document.createElement("tr");
    columns.forEach(col => {
      const th = document.createElement("th");
      th.textContent = col.label;
      if (col.sortable === false){
        th.style.cursor = "default";
      } else {
        th.addEventListener("click", () => {
          if (sortKey === col.key) sortDir = (sortDir === "asc" ? "desc" : "asc");
          else { sortKey = col.key; sortDir = col.defaultDir || "desc"; }
          renderBody();
          // update hints
          $all("thead th").forEach(x => x.querySelector(".hint")?.remove());
          th.appendChild(makeHint(sortDir));
        });
      }
      if (col.align) th.style.textAlign = col.align;
      if (sortKey === col.key) th.appendChild(makeHint(sortDir));
      tr.appendChild(th);
    });
    thead.appendChild(tr);
  };

  const makeHint = (dir) => {
    const span = document.createElement("span");
    span.className = "hint";
    span.textContent = dir === "asc" ? "▲" : "▼";
    return span;
  };

  const getSortVal = (r) => {
    const col = columns.find(c => c.key === sortKey) || {};
    const raw = r[sortKey];
    if (col.sortType === "number") return Number(raw);
    return normalizeText(raw);
  };

  const renderBody = (filtered=null) => {
    const data = (filtered ?? rows).slice();
    if (sortKey){
      data.sort((a,b) => {
        const va = getSortVal(a);
        const vb = getSortVal(b);
        if (Number.isNaN(va) && Number.isNaN(vb)) return 0;
        if (Number.isNaN(va)) return 1;
        if (Number.isNaN(vb)) return -1;
        if (va < vb) return sortDir === "asc" ? -1 : 1;
        if (va > vb) return sortDir === "asc" ? 1 : -1;
        return 0;
      });
    }

    tbody.innerHTML = "";
    data.forEach((r, idx) => {
      const tr = document.createElement("tr");
      if (rowIdKey && r[rowIdKey]) tr.dataset.rowid = r[rowIdKey];
      columns.forEach(col => {
        const td = document.createElement("td");
        let value = r[col.key];
        if (col.compute) value = col.compute(r, idx);
        if (col.format) value = col.format(value, r, idx);
        td.textContent = value ?? "—";
        if (col.className) td.className = col.className;
        if (col.align) td.classList.add(col.align === "right" ? "right" : col.align === "center" ? "center" : "");
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  };

  renderHead();
  renderBody();

  table.appendChild(thead);
  table.appendChild(tbody);

  const api = {
    el: table,
    setRows(newRows){
      rows = newRows;
      renderBody();
    },
    filterByText(q, filterKeys=null){
      const qq = normalizeText(q);
      if (!qq){
        renderBody();
        return;
      }
      const keys = filterKeys?.length ? filterKeys : columns.map(c=>c.key);
      const filtered = rows.filter(r => {
        const hay = keys.map(k => normalizeText(r[k])).join(" ");
        return hay.includes(qq);
      });
      renderBody(filtered);
    }
  };

  return api;
}

export function renderKpis(container, kpis){
  const wrap = document.createElement("div");
  wrap.className = "kpis";
  kpis.forEach(k => {
    const el = document.createElement("div");
    el.className = "kpi";
    el.innerHTML = `<div class="label">${k.label}</div><div class="value ${k.accent ? "orange": ""}">${k.value}</div>`;
    wrap.appendChild(el);
  });
  container.appendChild(wrap);
}
