const CSV_URL = "member_ranking_export.csv";

const state = {
  rows: [],
  filtered: [],
  search: "",
  minGames: 0,
};

const $body = document.getElementById("rankingBody");
const $search = document.getElementById("search");
const $minGames = document.getElementById("minGames");
const $playerCount = document.getElementById("playerCount");

async function loadCsv() {
  try {
    const res = await fetch(CSV_URL);
    if (!res.ok) {
      throw new Error("Falha ao carregar CSV: " + res.status);
    }
    const text = await res.text();
    parseCsv(text);
    applyFiltersAndRender();
  } catch (err) {
    console.error(err);
    $body.innerHTML =
      '<tr><td colspan="4">Erro ao carregar Dados.</td></tr>';
  }
}

function parseCsv(text) {
  const lines = text.trim().split("\n");
  if (lines.length < 2) return;

  const header = lines[0].split(",").map((h) => h.trim());

  const idxPos = header.indexOf("position");
  const idxNick = header.indexOf("nick");
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
    const puuid = cols[idxPuuid]; // ainda carregamos, só não exibimos
    const matches = Number(cols[idxMatches]);
    const meanFinalScore = Number(cols[idxMean]);

    rows.push({
      position,
      nick,
      puuid,
      matches,
      meanFinalScore,
    });
  }

  rows.sort((a, b) => a.position - b.position);
  state.rows = rows;
}

function applyFiltersAndRender() {
  const search = state.search.toLowerCase();
  const minGames = state.minGames;

  const filtered = state.rows.filter((r) => {
    const matchesSearch = !search || r.nick.toLowerCase().includes(search);
    const matchesGames = r.matches >= minGames;
    return matchesSearch && matchesGames;
  });

  state.filtered = filtered;
  $playerCount.textContent = filtered.length.toString();
  renderTable();
}

function renderTable() {
  if (!state.filtered.length) {
    $body.innerHTML =
      '<tr><td colspan="4">Nenhum jogador encontrado com esses filtros.</td></tr>';
    return;
  }

  const rowsHtml = state.filtered
    .map((row) => {
      const pos = row.position;
      const nick = row.nick;
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

      return `
        <tr class="${rowClass}">
          <td class="pos">${medal}<span>${pos}º</span></td>
          <td class="nick">
            ${nick} ${badge ? " · " + badge : ""}
          </td>
          <td class="matches">${matches}</td>
          <td class="score">${score}</td>
        </tr>
      `;
    })
    .join("");

  $body.innerHTML = rowsHtml;
}

$search.addEventListener("input", (e) => {
  state.search = e.target.value || "";
  applyFiltersAndRender();
});

$minGames.addEventListener("input", (e) => {
  const val = Number(e.target.value || 0);
  state.minGames = isNaN(val) ? 0 : val;
  applyFiltersAndRender();
});

loadCsv();
