import { fetchCSV, createTable, makeSearch, formatNumber, formatInt, teamPositionLabel, setActiveNav, renderKpis } from "../common.js";

setActiveNav("matches");

const URL_MATCHES = new URL('../../data/match_individual_score_grouped_export.csv', import.meta.url);

function safeParsePlayersScores(raw){
  try{
    if (!raw) return [];
    return JSON.parse(raw);
  }catch(e){
    return [];
  }
}

function createMatchCard(match){
  const card = document.createElement("div");
  card.className = "match";

  const head = document.createElement("div");
  head.className = "match-head";

  const meta = document.createElement("div");
  meta.className = "match-meta";

  const title = document.createElement("div");
  title.className = "match-title";
  title.textContent = match.match_riot_id || `match_pk ${match.match_pk}`;

  const badges = document.createElement("div");
  badges.className = "match-meta";

  const bPlayers = document.createElement("span");
  bPlayers.className = "badge";
  bPlayers.innerHTML = `Jogadores <strong>${formatInt(match.players)}</strong>`;

  const bMean = document.createElement("span");
  bMean.className = "badge orange";
  bMean.innerHTML = `Média <strong>${formatNumber(match.meanFinalScore,{decimals:1})}</strong>`;

  const bMax = document.createElement("span");
  bMax.className = "badge";
  bMax.innerHTML = `Máx <strong>${formatNumber(match.maxFinalScore,{decimals:1})}</strong>`;

  badges.append(bPlayers,bMean,bMax);
  meta.append(title, badges);

  const chev = document.createElement("div");
  chev.className = "chev";
  chev.textContent = "⌄";

  head.append(meta, chev);

  const body = document.createElement("div");
  body.className = "match-body";

  const players = safeParsePlayersScores(match.players_scores);
  const rows = players.map((p,i)=> ({
    position: i+1,
    team_position: p.team_position,
    nick: p.nick,
    tag: p.tag,
    final_score: p.final_score
  }));

  const table = createTable({
    columns: [
      { key:"position", label:"#", sortType:"number", align:"right", format:(v)=> formatInt(v) },
      { key:"team_position", label:"Rota", compute:(r)=> teamPositionLabel(r.team_position) },
      { key:"nick", label:"Nick", compute:(r)=> `${r.nick}#${r.tag}` },
      { key:"final_score", label:"Score", sortType:"number", align:"right", format:(v)=> formatNumber(v,{decimals:1}) }
    ],
    rows,
    initialSortKey:"final_score",
    initialSortDir:"desc"
  });

  const wrap = document.createElement("div");
  wrap.className = "table-wrap";
  wrap.appendChild(table.el);
  body.appendChild(wrap);

  card.append(head, body);

  head.addEventListener("click", () => {
    card.classList.toggle("open");
  });

  return card;
}

(async function init(){
  const rows = await fetchCSV(URL_MATCHES);

  // KPIs
  const totalMatches = rows.length;
  const totalPlayers = rows.reduce((acc,r)=> acc + Number(r.players || 0), 0);
  const bestMax = rows.reduce((m,r)=> Math.max(m, Number(r.maxFinalScore||0)), 0);

  renderKpis(document.getElementById("kpis"), [
    { label:"Partidas", value: formatInt(totalMatches), accent:true },
    { label:"Jogadores (somados)", value: formatInt(totalPlayers) },
    { label:"Maior score individual", value: formatNumber(bestMax,{decimals:1}), accent:true }
  ]);

  const mount = document.getElementById("matches");
  const controls = document.getElementById("controls");

  // Search filters cards by riot id or nick in json string
  const {wrap:searchWrap, input} = makeSearch((q)=> {
    const qq = (q||"").toLowerCase();
    const cards = [...mount.children];
    cards.forEach(card => {
      const id = card.querySelector(".match-title")?.textContent?.toLowerCase() || "";
      const text = card.textContent.toLowerCase();
      card.style.display = (id.includes(qq) || text.includes(qq)) ? "" : "none";
    });
  }, "Pesquisar match id ou jogador...");
  controls.appendChild(searchWrap);

  const btn = document.createElement("button");
  btn.className = "btn";
  btn.textContent = "Limpar";
  btn.addEventListener("click", ()=> { input.value=""; input.dispatchEvent(new Event("input")); });
  controls.appendChild(btn);

  // Render
  mount.innerHTML = "";
  const sorted = rows.slice().sort((a,b)=> Number(b.match_pk||0)-Number(a.match_pk||0));
  sorted.forEach(m => mount.appendChild(createMatchCard(m)));

})().catch(err => {
  console.error(err);
  document.getElementById("page-error").textContent = `Erro ao carregar dados: ${err.message}`;
});
