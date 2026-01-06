import { fetchCSV, createTable, makeSearch, formatNumber, formatInt, setActiveNav, renderKpis } from "../common.js";

setActiveNav("ranking");

const DATA_URL = new URL('../../data/member_ranking_export.csv', import.meta.url);

(async function init(){
  const mount = document.getElementById("ranking-table");
  const kpiMount = document.getElementById("kpis");

  const rows = await fetchCSV(DATA_URL);

  // KPIs
  const totalPlayers = rows.length;
  const totalMatches = rows.reduce((acc,r)=> acc + Number(r.matches || 0), 0);
  const bestScore = rows.reduce((m,r)=> Math.max(m, Number(r.meanFinalScore||0)), 0);

  renderKpis(kpiMount, [
    { label:"Jogadores", value: formatInt(totalPlayers), accent:true },
    { label:"Jogos (somados)", value: formatInt(totalMatches) },
    { label:"Melhor score médio", value: formatNumber(bestScore,{decimals:1}) , accent:true }
  ]);

  const table = createTable({
    columns: [
      { key:"position", label:"#", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key:"nick", label:"Nick", compute:(r)=> `${r.nick}#${r.tag}` },
      { key:"matches", label:"P", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key:"meanFinalScore", label:"Score", sortType:"number", align:"right", format:(v)=> formatNumber(v,{decimals:1}) },
    ],
    rows,
    initialSortKey:"meanFinalScore",
    initialSortDir:"desc"
  });

  const controls = document.getElementById("controls");
  const {wrap:searchWrap, input} = makeSearch((q)=> table.filterByText(q, ["nick","tag"]), "Pesquisar jogador...");
  controls.appendChild(searchWrap);

  const btn = document.createElement("button");
  btn.className = "btn";
  btn.textContent = "Limpar";
  btn.addEventListener("click", ()=> { input.value=""; table.filterByText(""); });
  controls.appendChild(btn);

  const wrap = document.createElement("div");
  wrap.className = "table-wrap";
  wrap.appendChild(table.el);
  mount.appendChild(wrap);
})().catch(err => {
  console.error(err);
  document.getElementById("ranking-table").innerHTML = `<div class="small">Erro ao carregar dados: ${err.message}</div>`;
});
