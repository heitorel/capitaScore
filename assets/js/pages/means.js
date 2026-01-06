import { fetchCSV, createTable, makeSearch, formatNumber, formatInt, setActiveNav, renderKpis } from "../common.js";

setActiveNav("means");

const URL_KDA = new URL('../../data/ranking_kda_mean_export.csv', import.meta.url);
const URL_DMG = new URL('../../data/ranking_damage_mean_export.csv', import.meta.url);

function buildPlayerLabel(r){ return `${r.nick}#${r.tag}`; }

async function buildTable(mountId, rows, metricKey, metricLabel, formatMetric, searchPlaceholder){
  const mount = document.getElementById(mountId);
  const controls = mount.querySelector("[data-controls]");
  const tableHost = mount.querySelector("[data-table]");

  const table = createTable({
    columns: [
      { key:"position", label:"#", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key:"nick", label:"Nick", compute:(r)=> buildPlayerLabel(r) },
      { key:"matches", label:"P", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key: metricKey, label: metricLabel, sortType:"number", align:"right", format: formatMetric },
      { key:"meanFinalScore", label:"Score", sortType:"number", align:"right", format:(v)=> formatNumber(v,{decimals:1}) },
    ],
    rows,
    initialSortKey: metricKey,
    initialSortDir:"desc"
  });

  const {wrap:searchWrap, input} = makeSearch((q)=> table.filterByText(q, ["nick","tag"]), searchPlaceholder);
  controls.appendChild(searchWrap);

  const btn = document.createElement("button");
  btn.className = "btn";
  btn.textContent = "Limpar";
  btn.addEventListener("click", ()=> { input.value=""; table.filterByText(""); });
  controls.appendChild(btn);

  const wrap = document.createElement("div");
  wrap.className = "table-wrap";
  wrap.appendChild(table.el);
  tableHost.appendChild(wrap);

  return table;
}

(async function init(){
  const [kdaRows, dmgRows] = await Promise.all([fetchCSV(URL_KDA), fetchCSV(URL_DMG)]);

  // KPIs (global)
  const bestKda = kdaRows.reduce((m,r)=> Math.max(m, Number(r.meanKDA||0)), 0);
  const bestDmg = dmgRows.reduce((m,r)=> Math.max(m, Number(r.meanDmgPerMin||0)), 0);

  renderKpis(document.getElementById("kpis"), [
    { label:"Melhor KDA médio", value: formatNumber(bestKda,{decimals:2}), accent:true },
    { label:"Maior dano/min médio", value: formatNumber(bestDmg,{decimals:0}), accent:true },
    { label:"Jogadores no ranking", value: formatInt(Math.max(kdaRows.length, dmgRows.length)) }
  ]);

  await buildTable(
    "card-kda",
    kdaRows,
    "meanKDA",
    "KDA médio",
    (v)=> formatNumber(v,{decimals:2}),
    "Pesquisar jogador (KDA)..."
  );

  await buildTable(
    "card-dmg",
    dmgRows,
    "meanDmgPerMin",
    "Dano/min médio",
    (v)=> formatNumber(v,{decimals:0}),
    "Pesquisar jogador (Dano)..."
  );
})().catch(err => {
  console.error(err);
  document.getElementById("page-error").textContent = `Erro ao carregar dados: ${err.message}`;
});
