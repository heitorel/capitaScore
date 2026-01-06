import os
import json
import math

from typing import List, Dict, Any
from pathlib import Path

import pymysql

# pasta do projeto = pai da pasta "python"
BASE_DIR = Path(__file__).resolve().parent.parent

CSV_RANKING_EXPORT_PATH = BASE_DIR / "data" / "member_ranking_export.csv"
CSV_METRICS_EXPORT_PATH = BASE_DIR / "data" / "player_match_metrics_export.csv"

CSV_RANKING_KDA_MEAN_EXPORT_PATH = BASE_DIR / "data" / "ranking_kda_mean_export.csv"
CSV_RANKING_POSITION_SCORE_EXPORT_PATH = BASE_DIR / "data" / "ranking_position_score_export.csv"
CSV_RANKING_DAMAGE_MEAN_EXPORT_PATH = BASE_DIR / "data" / "ranking_damage_mean_export.csv"
CSV_RANKING_CHAMPION_WINRATE_EXPORT_PATH = BASE_DIR / "data" / "ranking_champion_winrate_export.csv"
CSV_RANKING_CHAMPION_KDA_EXPORT_PATH = BASE_DIR / "data" / "ranking_champion_kda_export.csv"
CSV_MATCH_INDIVIDUAL_SCORE_GROUPED_EXPORT_PATH = BASE_DIR / "data" / "match_individual_score_grouped_export.csv"

# =========================
# CONFIG DO BANCO
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


def win_to_int(raw_win) -> int:
    if raw_win is None:
        return 0
    if isinstance(raw_win, (int, float)):
        return 1 if raw_win != 0 else 0
    if isinstance(raw_win, (bytes, bytearray)):
        win_int = int.from_bytes(raw_win, byteorder="big")
        return 1 if win_int != 0 else 0
    s = str(raw_win).strip().lower()
    if s in ("1", "true", "win", "victory", "w"):
        return 1
    if s in ("0", "false", "loss", "defeat", "l", "fail", "f"):
        return 0
    return 0


# =========================
# ACESSO AO BANCO
# =========================

def get_connection():
    return pymysql.connect(**DB_CONFIG)


def fetch_members(conn):
    """
    Busca todos os membros ativos da tabela members.
    Retorna:
      - members_by_puuid: {puuid: {"member_id": ..., "nick": ...}}
      - puuid_set: set com todos os puuids de membros
    """
    sql = """
        SELECT id, puuid, nick
        FROM members
        WHERE active = 1
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    members_by_puuid: Dict[str, Dict[str, Any]] = {}
    puuid_set = set()
    for r in rows:
        puuid = r["puuid"]
        members_by_puuid[puuid] = {
            "member_id": r["id"],
            "nick": r["nick"],
        }
        puuid_set.add(puuid)

    return members_by_puuid, puuid_set


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
    Usa INSERT ... ON DUPLICATE KEY UPDATE.
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

def compute_metrics_for_match(
    match_row: Dict[str, Any],
    participants: List[Dict[str, Any]],
    member_puuids: set
) -> List[Dict[str, Any]]:
    """
    Calcula métricas para TODOS os participantes da partida (para normalização),
    mas só retorna linhas para quem está em member_puuids.
    """
    duration_sec = match_row["game_duration_sec"]
    if not duration_sec or duration_sec <= 0:
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
    team_kills: Dict[int, int] = {}
    for p in participants:
        team_id = p["team_id"]
        team_kills[team_id] = team_kills.get(team_id, 0) + (p.get("kills") or 0)

    # ---- Calcula métricas brutas por participante ----
    temp_rows: List[Dict[str, Any]] = []
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

        # participantId usado pela timeline (1..10)
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
            "is_member": puuid in member_puuids,
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

    if not temp_rows:
        return []

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
    metrics_rows: List[Dict[str, Any]] = []
    for i, base in enumerate(temp_rows):
        if not base["is_member"]:
            continue

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

        base.pop("is_member", None)

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
# RANKING DE MEMBROS
# =========================

def update_member_ranking(conn):
    """
    Calcula ranking por membro (apenas membros da tabela members)
    e grava em member_ranking_metrics.
    """
    sql = """
        SELECT m.id AS member_id,
               m.puuid AS puuid,
               m.nick AS nick,
               m.tag  AS tag,
               COUNT(pmm.id) AS matches_count,
               AVG(pmm.final_score) AS mean_final_score
        FROM player_match_metrics pmm
        JOIN members m ON m.puuid = pmm.puuid
        GROUP BY m.id, m.puuid, m.nick, m.tag
        ORDER BY mean_final_score DESC;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    if not rows:
        print("Nenhum dado para ranking de membros.")
        return

    ranking_rows = []
    position = 1
    for r in rows:
        ranking_rows.append({
            "member_id": r["member_id"],
            "puuid": r["puuid"],
            "nick": r["nick"],
            "tag":  r["tag"],
            "matches_count": int(r["matches_count"]),
            "mean_final_score": float(r["mean_final_score"]),
            "position": position,
        })
        position += 1

    sql_insert = """
        INSERT INTO member_ranking_metrics (
            member_id,
            puuid,
            nick,
            tag,
            matches_count,
            mean_final_score,
            position
        )
        VALUES (
            %(member_id)s,
            %(puuid)s,
            %(nick)s,
            %(tag)s,
            %(matches_count)s,
            %(mean_final_score)s,
            %(position)s
        )
        ON DUPLICATE KEY UPDATE
            puuid = VALUES(puuid),
            nick = VALUES(nick),
            tag  = VALUES(tag),
            matches_count = VALUES(matches_count),
            mean_final_score = VALUES(mean_final_score),
            position = VALUES(position);
    """
    with conn.cursor() as cur:
        cur.executemany(sql_insert, ranking_rows)
    conn.commit()

    print(f"Ranking de membros atualizado para {len(ranking_rows)} membros.")


# =========================
# EXPORTAR CSV (OPCIONAL)
# =========================

def export_metrics_to_csv(conn, path: Path = CSV_METRICS_EXPORT_PATH):
    """
    Exporta uma visão 'rica' de player_match_metrics para CSV:
    - junta com match_participants, matches e members
    - inclui nick, tag, team_position, win, champion, match_riot_id, created_at etc.

    Retorna a lista de rows já normalizada (win=0/1 e created_at em ISO)
    para reutilizar nos rankings sem novas queries.
    """
    sql = """
        SELECT
            pmm.id                          AS metrics_id,
            pmm.match_id                    AS match_pk,
            mt.match_id                     AS match_riot_id,
            pmm.puuid                       AS puuid,
            mem.nick                        AS nick,
            mem.tag                         AS tag,
            mp.team_position                AS team_position,
            mp.win                          AS win,
            mp.champion_name                AS champion_name,
            pmm.kda                         AS kda,
            pmm.dmg_per_min                 AS dmg_per_min,
            pmm.gold_per_min                AS gold_per_min,
            pmm.cs_per_min                  AS cs_per_min,
            pmm.kp                          AS kp,
            pmm.dmg_taken_per_min           AS dmg_taken_per_min,
            pmm.deaths_per_min              AS deaths_per_min,
            pmm.xp_per_min                  AS xp_per_min,
            pmm.vision_per_min              AS vision_per_min,
            pmm.cc_per_min                  AS cc_per_min,
            pmm.final_score                 AS final_score,
            pmm.created_at                  AS created_at
        FROM player_match_metrics pmm
        JOIN match_participants mp
          ON pmm.match_participant_id = mp.id
        JOIN matches mt
          ON pmm.match_id = mt.id
        LEFT JOIN members mem
          ON mem.puuid = pmm.puuid
        ORDER BY pmm.created_at DESC;
    """

    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    if not rows:
        print("Nenhum dado em player_match_metrics para exportar.")
        return []

    import csv

    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "metrics_id",
        "match_pk",
        "match_riot_id",
        "puuid",
        "nick",
        "tag",
        "team_position",
        "win",
        "champion_name",
        "kda",
        "dmg_per_min",
        "gold_per_min",
        "cs_per_min",
        "kp",
        "dmg_taken_per_min",
        "deaths_per_min",
        "xp_per_min",
        "vision_per_min",
        "cc_per_min",
        "final_score",
        "created_at",
    ]

    exported_rows = []

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            win_flag = win_to_int(r["win"])
            created_at_iso = r["created_at"].isoformat() if r["created_at"] else ""

            out_row = {
                "metrics_id": r["metrics_id"],
                "match_pk": r["match_pk"],
                "match_riot_id": r["match_riot_id"],
                "puuid": r["puuid"],
                "nick": r["nick"] or "",
                "tag": r["tag"] or "",
                "team_position": r["team_position"] or "",
                "win": win_flag,
                "champion_name": r["champion_name"],
                "kda": r["kda"],
                "dmg_per_min": r["dmg_per_min"],
                "gold_per_min": r["gold_per_min"],
                "cs_per_min": r["cs_per_min"],
                "kp": r["kp"],
                "dmg_taken_per_min": r["dmg_taken_per_min"],
                "deaths_per_min": r["deaths_per_min"],
                "xp_per_min": r["xp_per_min"],
                "vision_per_min": r["vision_per_min"],
                "cc_per_min": r["cc_per_min"],
                "final_score": r["final_score"],
                "created_at": created_at_iso,
            }

            writer.writerow(out_row)
            exported_rows.append(out_row)

    print(f"Exportado CSV de métricas para: {path}")
    return exported_rows


def export_ranking_to_csv(conn, path: Path = CSV_RANKING_EXPORT_PATH):
    """
    Exporta a tabela member_ranking_metrics (ranking dos membros)
    para CSV em assets/data/member_ranking_export.csv
    (usado pelo front).
    """
    sql = """
        SELECT
            position,
            nick,
            tag,
            puuid,
            matches_count,
            mean_final_score
        FROM member_ranking_metrics
        ORDER BY position ASC
    """

    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    if not rows:
        print("Nenhum dado em member_ranking_metrics para exportar.")
        return

    import csv

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["position", "nick", "tag", "puuid", "matches", "meanFinalScore"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in rows:
            writer.writerow({
                "position": r["position"],
                "nick": r["nick"],
                "tag":  r["tag"],
                "puuid": r["puuid"],
                "matches": r["matches_count"],
                "meanFinalScore": r["mean_final_score"],
            })

    print(f"Exportado CSV de ranking para: {path}")


# =========================
# NOVOS RANKINGS (sem novas queries)
# =========================

def export_ranking_kda_mean_to_csv(metrics_rows, path: Path = CSV_RANKING_KDA_MEAN_EXPORT_PATH):
    if not metrics_rows:
        print("Nenhum dado para ranking de KDA médio.")
        return

    import csv

    agg = {}
    for r in metrics_rows:
        key = (r["puuid"], r["nick"], r["tag"])
        if key not in agg:
            agg[key] = {"puuid": r["puuid"], "nick": r["nick"], "tag": r["tag"], "matches": 0, "sumKDA": 0.0, "sumFinalScore": 0.0}
        agg[key]["matches"] += 1
        agg[key]["sumKDA"] += float(r["kda"])
        agg[key]["sumFinalScore"] += float(r["final_score"])

    rows_out = []
    for _, s in agg.items():
        matches = s["matches"]
        rows_out.append({
            "nick": s["nick"],
            "tag": s["tag"],
            "puuid": s["puuid"],
            "matches": matches,
            "meanFinalScore": s["sumFinalScore"] / matches,
            "meanKDA": s["sumKDA"] / matches,
        })

    rows_out.sort(key=lambda x: x["meanKDA"], reverse=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["position", "nick", "tag", "puuid", "matches", "meanFinalScore", "meanKDA"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        pos = 1
        for r in rows_out:
            r["position"] = pos
            writer.writerow(r)
            pos += 1

    print(f"Exportado CSV ranking KDA médio para: {path}")


def export_ranking_position_score_to_csv(metrics_rows, path: Path = CSV_RANKING_POSITION_SCORE_EXPORT_PATH):
    if not metrics_rows:
        print("Nenhum dado para ranking por posição (team_position).")
        return

    import csv

    def map_pos(tp: str) -> str:
        s = (tp or "").strip().upper()
        if s in ("JUNGLE", "JG"):
            return "JG"
        if s in ("MIDDLE", "MID"):
            return "MID"
        if s in ("BOTTOM", "ADC"):
            return "ADC"
        if s in ("UTILITY", "SUP", "SUPPORT"):
            return "SUP"
        if s in ("TOP",):
            return "TOP"
        return s

    pos_order = {"TOP": 0, "JG": 1, "MID": 2, "ADC": 3, "SUP": 4}

    agg = {}
    for r in metrics_rows:
        tp = map_pos(r["team_position"])
        puuid = r["puuid"]
        nick = r["nick"]
        tag = r["tag"]

        key = (tp, puuid)
        if key not in agg:
            agg[key] = {
                "team_position": tp,
                "puuid": puuid,
                "nick_tag": f"{nick}#{tag}" if tag else nick,
                "matches": 0,
                "sumFinalScore": 0.0,
            }

        agg[key]["matches"] += 1
        agg[key]["sumFinalScore"] += float(r["final_score"])

    by_pos = {"TOP": [], "JG": [], "MID": [], "ADC": [], "SUP": []}
    for (_, _), s in agg.items():
        tp = s["team_position"]
        if tp not in by_pos:
            continue
        matches = s["matches"]
        by_pos[tp].append({
            "team_position": tp,
            "puuid": s["puuid"],
            "nick": s["nick_tag"],
            "matches": matches,
            "meanFinalScore": s["sumFinalScore"] / matches,
        })

    rows_out = []
    for tp in ["TOP", "JG", "MID", "ADC", "SUP"]:
        players = by_pos[tp]
        players.sort(key=lambda x: x["meanFinalScore"], reverse=True)
        pos = 1
        for p in players:
            p["position"] = pos
            rows_out.append(p)
            pos += 1

    rows_out.sort(key=lambda x: (pos_order.get(x["team_position"], 99), x["position"]))

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["team_position", "position", "nick", "matches", "meanFinalScore", "puuid"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows_out:
            writer.writerow(r)

    print(f"Exportado CSV ranking por posição (player rank por team_position) para: {path}")

def export_ranking_damage_mean_to_csv(metrics_rows, path: Path = CSV_RANKING_DAMAGE_MEAN_EXPORT_PATH):
    if not metrics_rows:
        print("Nenhum dado para ranking de dano médio.")
        return

    import csv

    agg = {}
    for r in metrics_rows:
        key = (r["puuid"], r["nick"], r["tag"])
        if key not in agg:
            agg[key] = {"puuid": r["puuid"], "nick": r["nick"], "tag": r["tag"], "matches": 0, "sumDmg": 0.0, "sumFinalScore": 0.0}
        agg[key]["matches"] += 1
        agg[key]["sumDmg"] += float(r["dmg_per_min"])
        agg[key]["sumFinalScore"] += float(r["final_score"])

    rows_out = []
    for _, s in agg.items():
        matches = s["matches"]
        rows_out.append({
            "nick": s["nick"],
            "tag": s["tag"],
            "puuid": s["puuid"],
            "matches": matches,
            "meanFinalScore": s["sumFinalScore"] / matches,
            "meanDmgPerMin": s["sumDmg"] / matches,
        })

    rows_out.sort(key=lambda x: x["meanDmgPerMin"], reverse=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["position", "nick", "tag", "puuid", "matches", "meanFinalScore", "meanDmgPerMin"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        pos = 1
        for r in rows_out:
            r["position"] = pos
            writer.writerow(r)
            pos += 1

    print(f"Exportado CSV ranking dano médio para: {path}")


def export_ranking_champion_winrate_to_csv(metrics_rows, path: Path = CSV_RANKING_CHAMPION_WINRATE_EXPORT_PATH):
    if not metrics_rows:
        print("Nenhum dado para ranking winrate por campeão.")
        return

    import csv

    agg = {}
    for r in metrics_rows:
        champ = r["champion_name"]
        if champ not in agg:
            agg[champ] = {"champion_name": champ, "matches": 0, "wins": 0, "sumFinalScore": 0.0, "sumKDA": 0.0}
        agg[champ]["matches"] += 1
        agg[champ]["wins"] += int(r["win"])
        agg[champ]["sumFinalScore"] += float(r["final_score"])
        agg[champ]["sumKDA"] += float(r["kda"])

    rows_out = []
    for _, s in agg.items():
        matches = s["matches"]
        wins = s["wins"]
        rows_out.append({
            "champion_name": s["champion_name"],
            "matches": matches,
            "wins": wins,
            "winRate": (wins / matches) * 100.0,
            "meanFinalScore": s["sumFinalScore"] / matches,
            "meanKDA": s["sumKDA"] / matches,
        })

    rows_out.sort(key=lambda x: x["winRate"], reverse=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["position", "champion_name", "matches", "wins", "winRate", "meanFinalScore", "meanKDA"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        pos = 1
        for r in rows_out:
            r["position"] = pos
            writer.writerow(r)
            pos += 1

    print(f"Exportado CSV ranking winrate por campeão para: {path}")


def export_ranking_champion_kda_to_csv(metrics_rows, path: Path = CSV_RANKING_CHAMPION_KDA_EXPORT_PATH):
    if not metrics_rows:
        print("Nenhum dado para ranking KDA por campeão.")
        return

    import csv

    agg = {}
    for r in metrics_rows:
        champ = r["champion_name"]
        if champ not in agg:
            agg[champ] = {"champion_name": champ, "matches": 0, "wins": 0, "sumFinalScore": 0.0, "sumKDA": 0.0}
        agg[champ]["matches"] += 1
        agg[champ]["wins"] += int(r["win"])
        agg[champ]["sumFinalScore"] += float(r["final_score"])
        agg[champ]["sumKDA"] += float(r["kda"])

    rows_out = []
    for _, s in agg.items():
        matches = s["matches"]
        wins = s["wins"]
        rows_out.append({
            "champion_name": s["champion_name"],
            "matches": matches,
            "meanKDA": (s["sumKDA"] / matches),
            "winRate": (wins / matches) * 100.0,
            "meanFinalScore": s["sumFinalScore"] / matches,
        })

    rows_out.sort(key=lambda x: x["meanKDA"], reverse=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["position", "champion_name", "matches", "meanKDA", "winRate", "meanFinalScore"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        pos = 1
        for r in rows_out:
            r["position"] = pos
            writer.writerow(r)
            pos += 1

    print(f"Exportado CSV ranking KDA por campeão para: {path}")


def export_match_individual_score_grouped_to_csv(metrics_rows, path: Path = CSV_MATCH_INDIVIDUAL_SCORE_GROUPED_EXPORT_PATH):
    if not metrics_rows:
        print("Nenhum dado para score individual agrupado por match.")
        return

    import csv

    matches = {}
    for r in metrics_rows:
        match_pk = r["match_pk"]
        if match_pk not in matches:
            matches[match_pk] = {
                "match_pk": r["match_pk"],
                "match_riot_id": r["match_riot_id"],
                "created_at": r["created_at"],
                "players": [],
            }

        matches[match_pk]["players"].append({
            "team_position": r["team_position"],
            "nick": r["nick"],
            "tag": r["tag"],
            "puuid": r["puuid"],
            "win": int(r["win"]),
            "champion_name": r["champion_name"],
            "kda": float(r["kda"]),
            "dmg_per_min": float(r["dmg_per_min"]),
            "final_score": float(r["final_score"]),
        })

    rows_out = []
    for _, m in matches.items():
        players = m["players"]
        players.sort(key=lambda x: x["final_score"], reverse=True)

        sum_score = 0.0
        max_score = None
        for p in players:
            sum_score += p["final_score"]
            if max_score is None or p["final_score"] > max_score:
                max_score = p["final_score"]

        mean_score = sum_score / len(players) if players else 0.0

        rows_out.append({
            "match_pk": m["match_pk"],
            "match_riot_id": m["match_riot_id"],
            "created_at": m["created_at"],
            "players": len(players),
            "meanFinalScore": mean_score,
            "maxFinalScore": max_score if max_score is not None else 0.0,
            "players_scores": json.dumps(players, ensure_ascii=False),
        })

    rows_out.sort(key=lambda x: x["created_at"], reverse=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["match_pk", "match_riot_id", "created_at", "players", "meanFinalScore", "maxFinalScore", "players_scores"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows_out:
            writer.writerow(r)

    print(f"Exportado CSV score individual agrupado por partidas para: {path}")


# =========================
# MAIN
# =========================

def main():
    conn = get_connection()
    try:
        members_by_puuid, member_puuids = fetch_members(conn)
        print(f"Encontrados {len(member_puuids)} membros ativos na tabela members.")

        matches = fetch_matches_to_process(conn)
        print(f"Encontradas {len(matches)} partidas para processar.")

        for m in matches:
            print(f"Processando match {m['match_id_riot']} (id={m['match_pk']})...")
            participants = fetch_participants_for_match(conn, m["match_pk"])
            if not participants:
                print("  -> sem participantes? pulando.")
                continue

            metrics_rows = compute_metrics_for_match(m, participants, member_puuids)
            if not metrics_rows:
                print("  -> nenhum membro do grupo nessa partida. pulando.")
                continue

            insert_metrics(conn, metrics_rows)
            print(f"  -> inseridas {len(metrics_rows)} linhas em player_match_metrics.")

        # Atualiza ranking por membro
        update_member_ranking(conn)

        # Exportar CSV
        exported_metrics_rows = export_metrics_to_csv(conn)
        export_ranking_to_csv(conn)

        # Novos rankings (sem novas queries)
        export_ranking_kda_mean_to_csv(exported_metrics_rows)
        export_ranking_position_score_to_csv(exported_metrics_rows)
        export_ranking_damage_mean_to_csv(exported_metrics_rows)
        export_ranking_champion_winrate_to_csv(exported_metrics_rows)
        export_ranking_champion_kda_to_csv(exported_metrics_rows)
        export_match_individual_score_grouped_to_csv(exported_metrics_rows)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
