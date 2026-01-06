import {
  fetchCSV,
  createTable,
  makeSearch,
  formatNumber,
  formatInt,
  formatPercent,
  setActiveNav,
  renderKpis
} from "../common.js";

setActiveNav("champions");

const URL_WR  = new URL("../../data/ranking_champion_winrate_export.csv", import.meta.url);
const URL_KDA = new URL("../../data/ranking_champion_kda_export.csv", import.meta.url);

async function buildTable(mountId, rows, columns, initialSortKey, searchKeys, searchPlaceholder){
  const mount = document.getElementById(mountId);
  const controls = mount.querySelector("[data-controls]");
  const tableHost = mount.querySelector("[data-table]");

  const table = createTable({
    columns,
    rows,
    initialSortKey,
    initialSortDir: "desc"
  });

  const {wrap:searchWrap, input} = makeSearch(
    (q)=> table.filterByText(q, searchKeys),
    searchPlaceholder
  );
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
}

(async function init(){
  const [wrRows, kdaRows] = await Promise.all([fetchCSV(URL_WR), fetchCSV(URL_KDA)]);

  // KPIs
  const bestWR = wrRows.reduce((m,r)=> Math.max(m, Number(r.winRate || 0)), 0);
  const bestKDA = kdaRows.reduce((m,r)=> Math.max(m, Number(r.meanKDA || 0)), 0);
  const mostPlayed = wrRows.reduce((m,r)=> Math.max(m, Number(r.matches || 0)), 0);

  renderKpis(document.getElementById("kpis"), [
    { label:"Maior win rate", value: formatPercent(bestWR,{decimals:1}), accent:true },
    { label:"Maior KDA por campeão", value: formatNumber(bestKDA,{decimals:2}), accent:true },
    { label:"Maior nº de jogos (campeão)", value: formatInt(mostPlayed) }
  ]);

  await buildTable(
    "card-winrate",
    wrRows,
    [
      { key:"position", label:"#", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key:"champion_name", label:"Campeão" },
      { key:"matches", label:"Jogos", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key:"wins", label:"Vitórias", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key:"winRate", label:"Win rate", sortType:"number", align:"right", format:(v)=> formatPercent(v,{decimals:1}) },
      { key:"meanKDA", label:"KDA médio", sortType:"number", align:"right", format:(v)=> formatNumber(v,{decimals:2}) },
      { key:"meanFinalScore", label:"Score", sortType:"number", align:"right", format:(v)=> formatNumber(v,{decimals:1}) }
    ],
    "winRate",
    ["champion_name"],
    "Pesquisar campeão (Win rate)..."
  );

  await buildTable(
    "card-kda",
    kdaRows,
    [
      { key:"position", label:"#", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key:"champion_name", label:"Campeão" },
      { key:"matches", label:"Jogos", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key:"meanKDA", label:"KDA médio", sortType:"number", align:"right", format:(v)=> formatNumber(v,{decimals:2}) },
      { key:"winRate", label:"Win rate", sortType:"number", align:"right", format:(v)=> formatPercent(v,{decimals:1}) },
      { key:"meanFinalScore", label:"Score", sortType:"number", align:"right", format:(v)=> formatNumber(v,{decimals:1}) }
    ],
    "meanKDA",
    ["champion_name"],
    "Pesquisar campeão (KDA)..."
  );
})().catch(err => {
  console.error(err);
  document.getElementById("page-error").textContent = `Erro ao carregar dados: ${err.message}`;
});
