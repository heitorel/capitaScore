import { fetchCSV, createTable, makeSearch, formatNumber, formatInt, teamPositionLabel, setActiveNav } from "../common.js";

setActiveNav("roles");

// Baseado na URL do HTML (roles.html). Assim o fetch SEMPRE acontece.
const CSV = new URL("../data/ranking_position_score_export.csv", window.location.href);

function canonicalRole(v){
  const raw = String(v ?? "").trim();
  if (!raw) return "—";
  const k = raw.toUpperCase();
  const m = {
    "TOP":"TOP",
    "JG":"JG",
    "JUNGLE":"JG",
    "MID":"MID",
    "MIDDLE":"MID",
    "ADC":"ADC",
    "BOTTOM":"ADC",
    "BOT":"ADC",
    "SUP":"SUP",
    "UTILITY":"SUP",
    "SUPPORT":"SUP",
  };
  return m[k] || raw;
}

function renderRoleSection(roleKey, rows){
  const section = document.createElement("div");
  section.className = "card";

  const header = document.createElement("div");
  header.className = "card-header";
  header.innerHTML = `
    <div>
      <h2>${teamPositionLabel(roleKey)}</h2>
      <div class="sub">Ranking por score (posição)</div>
    </div>
    <span class="badge orange">Players <strong>${formatInt(rows.length)}</strong></span>
  `;
  section.appendChild(header);

  const body = document.createElement("div");
  body.className = "card-body";

  const controls = document.createElement("div");
  controls.className = "controls";

  const table = createTable({
    columns: [
      { key:"position", label:"#", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key:"nick", label:"Nick" },
      { key:"matches", label:"P", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key:"meanFinalScore", label:"Score", sortType:"number", align:"right", format:(v)=> formatNumber(v,{decimals:1}) }
    ],
    rows,
    initialSortKey:"meanFinalScore",
    initialSortDir:"desc"
  });

  const {wrap:searchWrap, input} = makeSearch((q)=> table.filterByText(q, ["nick"]), `Pesquisar (${teamPositionLabel(roleKey)})...`);
  const btn = document.createElement("button");
  btn.className = "btn";
  btn.textContent = "Limpar";
  btn.addEventListener("click", ()=> { input.value=""; table.filterByText(""); });

  controls.appendChild(searchWrap);
  controls.appendChild(btn);

  const wrap = document.createElement("div");
  wrap.className = "table-wrap";
  wrap.appendChild(table.el);

  body.appendChild(controls);
  body.appendChild(wrap);
  section.appendChild(body);

  return section;
}

(async function init(){
  console.log("[roles] CSV ->", CSV.href);

  const raw = await fetchCSV(CSV);
  console.log("[roles] linhas:", raw.length, raw[0]);

  const rows = raw.map(r => ({
    ...r,
    team_position: canonicalRole(r.team_position),
    position: Number(r.position),
    matches: Number(r.matches),
    meanFinalScore: Number(r.meanFinalScore)
  }));

  const grouped = new Map();
  for (const r of rows){
    const key = r.team_position || "—";
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(r);
  }

  const order = ["TOP","JG","MID","ADC","SUP"];
  const mount = document.getElementById("roles");
  mount.innerHTML = "";

  for (const key of order){
    if (grouped.has(key)) mount.appendChild(renderRoleSection(key, grouped.get(key)));
  }
  for (const [k,v] of grouped.entries()){
    if (!order.includes(k)) mount.appendChild(renderRoleSection(k, v));
  }
})().catch(err => {
  console.error(err);
  document.getElementById("page-error").textContent = `Erro ao carregar dados: ${err.message}`;
});
