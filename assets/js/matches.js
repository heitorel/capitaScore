const METRICS_CSV_URL = "./assets/data/player_match_metrics_export.csv";

const state = {
  rows: [],
  filtered: [],
  playerFilter: "",
  champFilter: "",
  resultFilter: "",
};

const $body = document.getElementById("matchesBody");
const $playerFilter = document.getElementById("playerFilter");
const $champFilter = document.getElementById("champFilter");
const $resultFilter = document.getElementById("resultFilter");

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

async function loadMetricsCsv() {
  try {
    const res = await fetch(METRICS_CSV_URL);
    if (!res.ok) {
      throw new Error("Erro ao carregar CSV de partidas");
    }
    const text = await res.text();
    parseMetricsCsv(text);
    applyFiltersAndRender();
  } catch (err) {
    console.error(err);
    $body.innerHTML =
      "<tr><td colspan='7'>Erro ao carregar CSV de partidas.</td></tr>";
  }
}

function parseMetricsCsv(text) {
  const lines = text.trim().split("\n");
  if (lines.length < 2) return;

  const header = lines[0].split(",").map((h) => h.trim());
  const idxNick = header.indexOf("nick");
  const idxTag = header.indexOf("tag");
  const idxRole = header.indexOf("team_position");
  const idxChamp = header.indexOf("champion_name");
  const idxKda = header.indexOf("kda");
  const idxScore = header.indexOf("final_score");
  const idxWin = header.indexOf("win");
  const idxCreated = header.indexOf("created_at");

  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    const cols = line.split(",");

    rows.push({
      nick: cols[idxNick] || "",
      tag: cols[idxTag] || "",
      role: mapRole(cols[idxRole]),
      champion: cols[idxChamp] || "",
      kda: parseFloat(cols[idxKda]) || 0,
      finalScore: parseFloat(cols[idxScore]) || 0,
      win: cols[idxWin] === "1",
      created_at: cols[idxCreated] || "",
    });
  }

  state.rows = rows;
}

function applyFiltersAndRender() {
  const playerF = state.playerFilter.toLowerCase();
  const champF = state.champFilter.toLowerCase();
  const resultF = state.resultFilter;

  state.filtered = state.rows.filter((r) => {
    if (playerF && !`${r.nick}`.toLowerCase().includes(playerF)) return false;
    if (champF && !r.champion.toLowerCase().includes(champF)) return false;
    if (resultF === "win" && !r.win) return false;
    if (resultF === "loss" && r.win) return false;
    return true;
  });

  renderTable();
}

function renderTable() {
  if (!state.filtered.length) {
    $body.innerHTML =
      "<tr><td colspan='7'>Nenhuma partida encontrada.</td></tr>";
    return;
  }

  const html = state.filtered
    .map((r) => {
      const dateStr = r.created_at
        ? new Date(r.created_at).toLocaleString("pt-BR")
        : "-";
      const resultLabel = r.win ? "Vitória" : "Derrota";
      const resultClass = r.win ? "result-win" : "result-loss";

      return `
        <tr>
          <td>${dateStr}</td>
          <td>${r.nick}${r.tag ? "#" + r.tag : ""}</td>
          <td>${r.role || "-"}</td>
          <td>${r.champion}</td>
          <td>${r.kda.toFixed(2)}</td>
          <td>${r.finalScore.toFixed(1)}</td>
          <td class="${resultClass}">${resultLabel}</td>
        </tr>
      `;
    })
    .join("");

  $body.innerHTML = html;
}

// listeners
$playerFilter.addEventListener("input", (e) => {
  state.playerFilter = e.target.value || "";
  applyFiltersAndRender();
});

$champFilter.addEventListener("input", (e) => {
  state.champFilter = e.target.value || "";
  applyFiltersAndRender();
});

$resultFilter.addEventListener("change", (e) => {
  state.resultFilter = e.target.value;
  applyFiltersAndRender();
});

// init
loadMetricsCsv();
