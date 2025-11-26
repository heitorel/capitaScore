// Caminhos dos CSVs (relativo ao index.html)
const RANKING_CSV_URL = "./assets/data/member_ranking_export.csv";
const METRICS_CSV_URL = "./assets/data/player_match_metrics_export.csv";

// Estado global simples
const state = {
  rankingRows: [],
  filteredRanking: [],
  metricsRows: [],
  roleRanking: null,
  mvpWeek: null,
  search: "",
  minGames: 0,
};

// DOM refs
const $rankingBody = document.getElementById("rankingBody");
const $search = document.getElementById("search");
const $minGames = document.getElementById("minGames");
const $playerCount = document.getElementById("playerCount");
const $mvpWeek = document.getElementById("mvp-week");

// role tables
const $roleTopBody = document.getElementById("roleTopBody");
const $roleJgBody = document.getElementById("roleJgBody");
const $roleMidBody = document.getElementById("roleMidBody");
const $roleAdcBody = document.getElementById("roleAdcBody");
const $roleSupBody = document.getElementById("roleSupBody");

function mapRole(raw) {
  switch ((raw || "").toUpperCase()) {
    case "TOP":
      return "TOP";
    case "JUNGLE":
      return "JG";
    case "MIDDLE":
      return "MID";
    case "BOTTOM":
      return "ADC";
    case "UTILITY":
      return "SUP";
    default:
      return "";
  }
}

async function init() {
  try {
    // carrega os dois CSVs em paralelo
    const [rankingText, metricsText] = await Promise.all([
      fetchText(RANKING_CSV_URL),
      fetchText(METRICS_CSV_URL),
    ]);

    parseRankingCsv(rankingText);
    parseMetricsCsv(metricsText);

    // monta ranking por rota + MVP da semana
    state.roleRanking = buildRoleRanking(state.metricsRows);
    state.mvpWeek = computeMvpOfWeek(state.metricsRows);

    applyFiltersAndRender();
    renderRoles();
    renderMvpCard();
  } catch (err) {
    console.error(err);
    $rankingBody.innerHTML =
      '<tr><td colspan="4">Erro ao carregar arquivos de ranking. Verifique se os CSVs existem em assets/data.</td></tr>';
  }
}

async function fetchText(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Falha ao carregar ${url}: ${res.status}`);
  }
  return res.text();
}

/* =========================
   PARSE CSVs
========================= */

function parseRankingCsv(text) {
  const lines = text.trim().split("\n");
  if (lines.length < 2) return;

  const header = lines[0].split(",").map((h) => h.trim());

  const idxPos = header.indexOf("position");
  const idxNick = header.indexOf("nick");
  const idxTag = header.indexOf("tag");
  const idxPuuid = header.indexOf("puuid");
  const idxMatches = header.indexOf("matches");
  const idxMean = header.indexOf("meanFinalScore");

  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const cols = line.split(",");

    const position = Number(cols[idxPos]);
    const nick = cols[idxNick];
    const tag = idxTag >= 0 ? cols[idxTag] : "";
    const puuid = cols[idxPuuid];
    const matches = Number(cols[idxMatches]);
    const meanFinalScore = Number(cols[idxMean]);

    rows.push({
      position,
      nick,
      tag,
      puuid,
      matches,
      meanFinalScore,
    });
  }

  rows.sort((a, b) => a.position - b.position);
  state.rankingRows = rows;
}

function parseMetricsCsv(text) {
  const lines = text.trim().split("\n");
  if (lines.length < 2) return;

  const header = lines[0].split(",").map((h) => h.trim());

  const idxNick = header.indexOf("nick");
  const idxTag = header.indexOf("tag");
  const idxRole = header.indexOf("team_position");
  const idxScore = header.indexOf("final_score");
  const idxWin = header.indexOf("win");
  const idxCreated = header.indexOf("created_at");

  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const cols = line.split(",");

    const nick = cols[idxNick] || "";
    const tag = cols[idxTag] || "";
    const roleRaw = cols[idxRole] || "";
    const role = mapRole(roleRaw);
    const finalScore = parseFloat(cols[idxScore]) || 0;
    const win = cols[idxWin] === "1";
    const created_at = cols[idxCreated] || "";

    // só membros (tem nick)
    if (!nick) continue;

    rows.push({
      nick,
      tag,
      role,
      finalScore,
      win,
      created_at,
    });
  }

  state.metricsRows = rows;
}

/* =========================
   RANKING GERAL
========================= */

function applyFiltersAndRender() {
  const search = state.search.toLowerCase();
  const minGames = state.minGames;

  const filtered = state.rankingRows.filter((r) => {
    const matchesSearch =
      !search || r.nick.toLowerCase().includes(search);
    const matchesGames = r.matches >= minGames;
    return matchesSearch && matchesGames;
  });

  state.filteredRanking = filtered;
  $playerCount.textContent = filtered.length.toString();
  renderRankingTable();
}

function renderRankingTable() {
  if (!state.filteredRanking.length) {
    $rankingBody.innerHTML =
      '<tr><td colspan="4">Nenhum jogador encontrado com esses filtros.</td></tr>';
    return;
  }

  const rowsHtml = state.filteredRanking
    .map((row) => {
      const pos = row.position;
      const nick = row.nick;
      const tag = row.tag || "";
      const matches = row.matches;
      const score = row.meanFinalScore.toFixed(2);

      let rowClass = "";
      let badge = "";
      if (pos === 1) {
        rowClass = "row-top1";
        badge = '<span class="badge-top1">MVP</span>';
      } else if (pos === 2) {
        rowClass = "row-top2";
        badge = '<span class="badge-top2">TOP 2</span>';
      } else if (pos === 3) {
        rowClass = "row-top3";
        badge = '<span class="badge-top3">TOP 3</span>';
      }

      const medal =
        pos === 1 ? "🥇" : pos === 2 ? "🥈" : pos === 3 ? "🥉" : "🔹";

      const riotId = tag ? `${nick}-${tag}` : nick;
      const riotIdSlug = encodeURIComponent(riotId);
      const opggUrl = `https://op.gg/pt/lol/summoners/BR/${riotIdSlug}`;

      return `
        <tr class="${rowClass}">
          <td class="pos">${medal}<span>${pos}º</span></td>
          <td class="nick">
            <a href="${opggUrl}"
               target="_blank"
               rel="noopener noreferrer"
               title="Ver ${nick}${tag ? "#" + tag : ""} no OP.GG">
              ${nick}${tag ? `<span class="tag">#${tag}</span>` : ""}
            </a>
            ${badge ? " · " + badge : ""}
          </td>
          <td class="matches">${matches}</td>
          <td class="score">${score}</td>
        </tr>
      `;
    })
    .join("");

  $rankingBody.innerHTML = rowsHtml;
}

/* =========================
   RANKING POR ROTA
========================= */

function buildRoleRanking(metricsRows) {
  const byKey = new Map();

  for (const row of metricsRows) {
    if (!row.nick) continue;
    if (!row.role) continue; // ignora UNKNOWN

    const key = `${row.nick}#${row.tag}|${row.role}`;
    const entry = byKey.get(key) || {
      nick: row.nick,
      tag: row.tag,
      role: row.role,
      matches: 0,
      sumScore: 0,
    };
    entry.matches += 1;
    entry.sumScore += row.finalScore;
    byKey.set(key, entry);
  }

  const list = Array.from(byKey.values()).map((e) => ({
    ...e,
    meanFinalScore: e.sumScore / e.matches,
  }));

  const roles = {
    TOP: [],
    JG: [],
    MID: [],
    ADC: [],
    SUP: [],
  };

  for (const e of list) {
    if (roles[e.role]) {
      roles[e.role].push(e);
    }
  }

  Object.keys(roles).forEach((role) => {
    roles[role].sort((a, b) => b.meanFinalScore - a.meanFinalScore);
  });

  return roles;
}

function renderRoleTable(rows, $tbody) {
  if (!$tbody) return;
  if (!rows || !rows.length) {
    $tbody.innerHTML = "<tr><td colspan='4'>Sem dados.</td></tr>";
    return;
  }

  const html = rows
    .map((row, index) => {
      const pos = index + 1;
      const nickTag = `${row.nick}${row.tag ? "#" + row.tag : ""}`;
      const score = row.meanFinalScore.toFixed(1);

      return `
        <tr>
          <td>${pos}</td>
          <td>${nickTag}</td>
          <td>${row.matches}</td>
          <td>${score}</td>
        </tr>
      `;
    })
    .join("");

  $tbody.innerHTML = html;
}

function renderRoles() {
  const r = state.roleRanking;
  if (!r) return;

  renderRoleTable(r.TOP, $roleTopBody);
  renderRoleTable(r.JG, $roleJgBody);
  renderRoleTable(r.MID, $roleMidBody);
  renderRoleTable(r.ADC, $roleAdcBody);
  renderRoleTable(r.SUP, $roleSupBody);
}

/* =========================
   MVP DA SEMANA
========================= */

function computeMvpOfWeek(metricsRows, minMatches = 3) {
  const now = new Date();
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

  const byPlayer = new Map();

  for (const row of metricsRows) {
    if (!row.nick || !row.created_at) continue;

    const createdAt = new Date(row.created_at);
    if (createdAt < weekAgo) continue;

    const key = `${row.nick}#${row.tag}`;
    const entry = byPlayer.get(key) || {
      nick: row.nick,
      tag: row.tag,
      matches: 0,
      sumScore: 0,
    };
    entry.matches += 1;
    entry.sumScore += row.finalScore;
    byPlayer.set(key, entry);
  }

  let best = null;

  for (const entry of byPlayer.values()) {
    if (entry.matches < minMatches) continue;
    const mean = entry.sumScore / entry.matches;
    if (!best || mean > best.meanFinalScore) {
      best = { ...entry, meanFinalScore: mean };
    }
  }

  return best;
}

function renderMvpCard() {
  if (!$mvpWeek) return;
  const mvp = state.mvpWeek;
  if (!mvp) {
    $mvpWeek.innerHTML =
      '<div class="mvp-card"><p>Nenhum MVP na semana (poucas partidas recentes).</p></div>';
    return;
  }

  $mvpWeek.innerHTML = `
    <div class="mvp-card">
      <h3>🔥 MVP da Semana</h3>
      <p><strong>${mvp.nick}${mvp.tag ? "#" + mvp.tag : ""}</strong></p>
      <p>${mvp.matches} partidas · média ${mvp.meanFinalScore.toFixed(1)}</p>
      <small>Considerando apenas membros com pelo menos 3 jogos nos últimos 7 dias.</small>
    </div>
  `;
}

/* =========================
   LISTENERS
========================= */

$search.addEventListener("input", (e) => {
  state.search = e.target.value || "";
  applyFiltersAndRender();
});

$minGames.addEventListener("input", (e) => {
  const val = Number(e.target.value || 0);
  state.minGames = isNaN(val) ? 0 : val;
  applyFiltersAndRender();
});

/* =========================
   START
========================= */

init();
