import os
import json
import math
import pymysql
from typing import List, Dict, Any

# =========================
# CONFIGURAÇÃO DO BANCO
# =========================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "admin"),
    "database": os.getenv("DB_NAME", "capitascore"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

# =========================
# PESOS DAS MÉTRICAS
# =========================

WEIGHTS = {
    "kda":               0.12,
    "dmg_per_min":       0.10,
    "gold_per_min":      0.08,
    "cs_per_min":        0.08,
    "kp":                0.10,
    "dmg_taken_per_min": 0.07,
    "deaths_per_min":    0.10,
    "xp_per_min":        0.10,
    "vision_per_min":    0.10,
    "cc_per_min":        0.15,
}


# =========================
# FUNÇÕES AUXILIARES
# =========================

def normalize_metric(values: List[float], invert: bool = False) -> List[float]:
    """
    Normaliza uma lista de valores para 0–100.
    Se invert=True, valores menores são melhores (ex: deaths/min).
    """
    if not values:
        return []

    min_v = min(values)
    max_v = max(values)

    if math.isclose(max_v, min_v):
        # todo mundo igual -> empate técnico
        return [50.0 for _ in values]

    scores = [(v - min_v) / (max_v - min_v) * 100.0 for v in values]
    if invert:
        scores = [100.0 - s for s in scores]
    return scores


# =========================
# ACESSO AO BANCO
# =========================

def get_connection():
    return pymysql.connect(**DB_CONFIG)


def fetch_matches_to_process(conn) -> List[Dict[str, Any]]:
    """
    Busca partidas que ainda não foram processadas em player_match_metrics.
    Critério: não existe nenhuma linha em player_match_metrics com aquele match_id.
    """
    sql = """
        SELECT m.id AS match_pk,
               m.match_id AS match_id_riot,
               m.game_duration AS game_duration_sec,
               t.raw_json AS timeline_json
        FROM matches m
        JOIN match_timelines t ON t.match_id = m.match_id
        LEFT JOIN player_match_metrics pmm ON pmm.match_id = m.id
        WHERE pmm.id IS NULL;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
    return rows


def fetch_participants_for_match(conn, match_pk: int) -> List[Dict[str, Any]]:
    """
    Busca todos os participantes de uma partida (match_participants).
    """
    sql = """
        SELECT *
        FROM match_participants
        WHERE match_id = %s
        ORDER BY participant_number ASC
    """
    with conn.cursor() as cur:
        cur.execute(sql, (match_pk,))
        rows = cur.fetchall()
    return rows


def insert_metrics(conn, metrics_rows: List[Dict[str, Any]]):
    """
    Insere os dados calculados em player_match_metrics.
    Usa INSERT ... ON DUPLICATE KEY UPDATE
    para não duplicar caso rode duas vezes.
    """
    if not metrics_rows:
        return

    sql = """
        INSERT INTO player_match_metrics (
            match_id,
            match_participant_id,
            puuid,
            team_id,
            champion_name,
            kda,
            dmg_per_min,
            gold_per_min,
            cs_per_min,
            kp,
            dmg_taken_per_min,
            deaths_per_min,
            xp_per_min,
            vision_per_min,
            cc_per_min,
            score_kda,
            score_dmg_per_min,
            score_gold_per_min,
            score_cs_per_min,
            score_kp,
            score_dmg_taken_per_min,
            score_deaths_per_min,
            score_xp_per_min,
            score_vision_per_min,
            score_cc_per_min,
            final_score
        )
        VALUES (
            %(match_id)s,
            %(match_participant_id)s,
            %(puuid)s,
            %(team_id)s,
            %(champion_name)s,
            %(kda)s,
            %(dmg_per_min)s,
            %(gold_per_min)s,
            %(cs_per_min)s,
            %(kp)s,
            %(dmg_taken_per_min)s,
            %(deaths_per_min)s,
            %(xp_per_min)s,
            %(vision_per_min)s,
            %(cc_per_min)s,
            %(score_kda)s,
            %(score_dmg_per_min)s,
            %(score_gold_per_min)s,
            %(score_cs_per_min)s,
            %(score_kp)s,
            %(score_dmg_taken_per_min)s,
            %(score_deaths_per_min)s,
            %(score_xp_per_min)s,
            %(score_vision_per_min)s,
            %(score_cc_per_min)s,
            %(final_score)s
        )
        ON DUPLICATE KEY UPDATE
            kda = VALUES(kda),
            dmg_per_min = VALUES(dmg_per_min),
            gold_per_min = VALUES(gold_per_min),
            cs_per_min = VALUES(cs_per_min),
            kp = VALUES(kp),
            dmg_taken_per_min = VALUES(dmg_taken_per_min),
            deaths_per_min = VALUES(deaths_per_min),
            xp_per_min = VALUES(xp_per_min),
            vision_per_min = VALUES(vision_per_min),
            cc_per_min = VALUES(cc_per_min),
            score_kda = VALUES(score_kda),
            score_dmg_per_min = VALUES(score_dmg_per_min),
            score_gold_per_min = VALUES(score_gold_per_min),
            score_cs_per_min = VALUES(score_cs_per_min),
            score_kp = VALUES(score_kp),
            score_dmg_taken_per_min = VALUES(score_dmg_taken_per_min),
            score_deaths_per_min = VALUES(score_deaths_per_min),
            score_xp_per_min = VALUES(score_xp_per_min),
            score_vision_per_min = VALUES(score_vision_per_min),
            score_cc_per_min = VALUES(score_cc_per_min),
            final_score = VALUES(final_score);
    """
    with conn.cursor() as cur:
        cur.executemany(sql, metrics_rows)
    conn.commit()


# =========================
# CÁLCULO DE MÉTRICAS POR PARTIDA
# =========================

def compute_metrics_for_match(match_row: Dict[str, Any],
                              participants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    duration_sec = match_row["game_duration_sec"]
    """
    Calcula as métricas para TODOS os participantes de uma partida.
    Usa:
      - match_participants (tabela)
      - timeline_json (para xp, CC, wards da timeline)
    """

    duration_sec = match_row["game_duration_sec"]
    if not duration_sec or duration_sec <= 0:
        # evita divisão por zero
        return []

    duration_min = duration_sec / 60.0

    # ---- Parse timeline JSON ----
    timeline = json.loads(match_row["timeline_json"])
    tl_meta = timeline["metadata"]
    tl_info = timeline["info"]

    # Mapa: puuid -> participantId (1..10)
    tl_puuids = tl_meta["participants"]
    puuid_to_pid = {puuid: idx + 1 for idx, puuid in enumerate(tl_puuids)}

    frames = tl_info["frames"]

    # Pré-cálculo: cc total e xp final por participantId
    cc_total_ms = {pid: 0 for pid in range(1, 11)}
    xp_final = {pid: 0 for pid in range(1, 11)}

    for frame in frames:
        pf = frame["participantFrames"]
        for pid_str, data in pf.items():
            pid = int(pid_str)
            cc_ms = data.get("timeEnemySpentControlled", 0)
            if cc_ms > cc_total_ms[pid]:
                cc_total_ms[pid] = cc_ms
            xp_final[pid] = data.get("xp", xp_final.get(pid, 0))

    # Wards da timeline (WARD_PLACED / WARD_KILL)
    wards_placed = {pid: 0 for pid in range(1, 11)}
    wards_killed = {pid: 0 for pid in range(1, 11)}

    for frame in frames:
        for event in frame.get("events", []):
            etype = event.get("type")
            if etype == "WARD_PLACED":
                creator = event.get("creatorId")
                if creator in wards_placed:
                    wards_placed[creator] += 1
            elif etype == "WARD_KILL":
                killer = event.get("killerId")
                if killer in wards_killed:
                    wards_killed[killer] += 1

    # ---- Team kills (para KP) ----
    team_kills = {}
    for p in participants:
        team_id = p["teamId"]
        team_kills[team_id] = team_kills.get(team_id, 0) + (p.get("kills") or 0)

    # ---- Calcula métricas brutas por participante ----
    temp_rows = []
    metrics_raw = {
        "kda": [],
        "dmg_per_min": [],
        "gold_per_min": [],
        "cs_per_min": [],
        "kp": [],
        "dmg_taken_per_min": [],
        "deaths_per_min": [],
        "xp_per_min": [],
        "vision_per_min": [],
        "cc_per_min": [],
    }

   for p in participants:
        puuid = p["puuid"]
        mp_id = p["id"]            # match_participants.id
        team_id = p["team_id"]
        champion_name = p["champion_name"]

        # participantId usado pela timeline
        pid = puuid_to_pid.get(puuid)
        if pid is None:
            continue

        kills = p.get("kills") or 0
        deaths = p.get("deaths") or 0
        assists = p.get("assists") or 0
        dmg_champs = p.get("total_damage_dealt_to_champions") or 0
        dmg_taken = p.get("total_damage_taken") or 0
        gold_earned = p.get("gold_earned") or 0
        total_minions = (p.get("total_minions_killed") or 0) + (p.get("neutral_minions_killed") or 0)

        # timeline based
        xp = xp_final[pid]
        cc_ms = cc_total_ms[pid]
        cc_s = cc_ms / 1000.0
        w_placed = wards_placed[pid]
        w_killed = wards_killed[pid]
        vision_actions = w_placed + w_killed

        # métricas por minuto
        dmg_per_min = dmg_champs / duration_min
        gold_per_min = gold_earned / duration_min
        cs_per_min = total_minions / duration_min
        dmg_taken_per_min = dmg_taken / duration_min
        deaths_per_min = deaths / duration_min
        xp_per_min = xp / duration_min
        vision_per_min = vision_actions / duration_min
        cc_per_min = cc_s / duration_min

        # KDA
        if deaths == 0:
            kda = kills + assists
        else:
            kda = (kills + assists) / deaths

        # Kill participation
        team_total_kills = team_kills.get(team_id, 0)
        kp = (kills + assists) / team_total_kills if team_total_kills > 0 else 0.0

        row = {
            "match_id": match_row["match_pk"],
            "match_participant_id": mp_id,
            "puuid": puuid,
            "team_id": team_id,
            "champion_name": champion_name,

            "kda": kda,
            "dmg_per_min": dmg_per_min,
            "gold_per_min": gold_per_min,
            "cs_per_min": cs_per_min,
            "kp": kp,
            "dmg_taken_per_min": dmg_taken_per_min,
            "deaths_per_min": deaths_per_min,
            "xp_per_min": xp_per_min,
            "vision_per_min": vision_per_min,
            "cc_per_min": cc_per_min,
        }

        temp_rows.append(row)

        metrics_raw["kda"].append(kda)
        metrics_raw["dmg_per_min"].append(dmg_per_min)
        metrics_raw["gold_per_min"].append(gold_per_min)
        metrics_raw["cs_per_min"].append(cs_per_min)
        metrics_raw["kp"].append(kp)
        metrics_raw["dmg_taken_per_min"].append(dmg_taken_per_min)
        metrics_raw["deaths_per_min"].append(deaths_per_min)
        metrics_raw["xp_per_min"].append(xp_per_min)
        metrics_raw["vision_per_min"].append(vision_per_min)
        metrics_raw["cc_per_min"].append(cc_per_min)

    # ---- Normalização por partida ----
    scores_norm = {
        "kda":               normalize_metric(metrics_raw["kda"], invert=False),
        "dmg_per_min":       normalize_metric(metrics_raw["dmg_per_min"], invert=False),
        "gold_per_min":      normalize_metric(metrics_raw["gold_per_min"], invert=False),
        "cs_per_min":        normalize_metric(metrics_raw["cs_per_min"], invert=False),
        "kp":                normalize_metric(metrics_raw["kp"], invert=False),
        "dmg_taken_per_min": normalize_metric(metrics_raw["dmg_taken_per_min"], invert=False),
        "deaths_per_min":    normalize_metric(metrics_raw["deaths_per_min"], invert=True),
        "xp_per_min":        normalize_metric(metrics_raw["xp_per_min"], invert=False),
        "vision_per_min":    normalize_metric(metrics_raw["vision_per_min"], invert=False),
        "cc_per_min":        normalize_metric(metrics_raw["cc_per_min"], invert=False),
    }

    # ---- Monta linhas finais com scores normalizados e final_score ----
    metrics_rows = []
    for i, base in enumerate(temp_rows):
        score_kda = scores_norm["kda"][i]
        score_dmg_per_min = scores_norm["dmg_per_min"][i]
        score_gold_per_min = scores_norm["gold_per_min"][i]
        score_cs_per_min = scores_norm["cs_per_min"][i]
        score_kp = scores_norm["kp"][i]
        score_dmg_taken_per_min = scores_norm["dmg_taken_per_min"][i]
        score_deaths_per_min = scores_norm["deaths_per_min"][i]
        score_xp_per_min = scores_norm["xp_per_min"][i]
        score_vision_per_min = scores_norm["vision_per_min"][i]
        score_cc_per_min = scores_norm["cc_per_min"][i]

        final_score = (
            WEIGHTS["kda"]               * score_kda +
            WEIGHTS["dmg_per_min"]       * score_dmg_per_min +
            WEIGHTS["gold_per_min"]      * score_gold_per_min +
            WEIGHTS["cs_per_min"]        * score_cs_per_min +
            WEIGHTS["kp"]                * score_kp +
            WEIGHTS["dmg_taken_per_min"] * score_dmg_taken_per_min +
            WEIGHTS["deaths_per_min"]    * score_deaths_per_min +
            WEIGHTS["xp_per_min"]        * score_xp_per_min +
            WEIGHTS["vision_per_min"]    * score_vision_per_min +
            WEIGHTS["cc_per_min"]        * score_cc_per_min
        )

        base.update({
            "score_kda":               score_kda,
            "score_dmg_per_min":       score_dmg_per_min,
            "score_gold_per_min":      score_gold_per_min,
            "score_cs_per_min":        score_cs_per_min,
            "score_kp":                score_kp,
            "score_dmg_taken_per_min": score_dmg_taken_per_min,
            "score_deaths_per_min":    score_deaths_per_min,
            "score_xp_per_min":        score_xp_per_min,
            "score_vision_per_min":    score_vision_per_min,
            "score_cc_per_min":        score_cc_per_min,
            "final_score":             final_score,
        })

        metrics_rows.append(base)

    return metrics_rows


# =========================
# EXPORTAR CSV (OPCIONAL)
# =========================

def export_metrics_to_csv(conn, path: str = "player_match_metrics_export.csv"):
    """
    Exporta a tabela player_match_metrics inteira para CSV.
    """
    sql = "SELECT * FROM player_match_metrics"
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    if not rows:
        print("Nenhum dado em player_match_metrics para exportar.")
        return

    import csv

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exportado CSV para: {path}")


# =========================
# MAIN
# =========================

def main():
    conn = get_connection()
    try:
        matches = fetch_matches_to_process(conn)
        print(f"Encontradas {len(matches)} partidas para processar.")

        for m in matches:
            print(f"Processando match {m['match_id_riot']} (id={m['match_pk']})...")
            participants = fetch_participants_for_match(conn, m["match_pk"])
            if not participants:
                print("  -> sem participantes? pulando.")
                continue

            metrics_rows = compute_metrics_for_match(m, participants)
            if not metrics_rows:
                print("  -> não foi possível calcular métricas. pulando.")
                continue

            insert_metrics(conn, metrics_rows)
            print(f"  -> inseridas {len(metrics_rows)} linhas em player_match_metrics.")

        # Exportar CSV opcional
        export_metrics_to_csv(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
