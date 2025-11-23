package com.capao.capitascore.domain.entity;

import com.capao.capitascore.common.BaseEntity;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(
        name = "player_match_metrics",
        uniqueConstraints = {
                @UniqueConstraint(
                        name = "uk_pmm_match_participant",
                        columnNames = {"match_id", "match_participant_id"}
                )
        },
        indexes = {
                @Index(name = "idx_pmm_match", columnList = "match_id"),
                @Index(name = "idx_pmm_match_participant", columnList = "match_participant_id"),
                @Index(name = "idx_pmm_puuid", columnList = "puuid")
        }
)
@Getter
@Setter
public class PlayerMatchMetrics extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "match_id", nullable = false)
    private Match match;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "match_participant_id", nullable = false)
    private MatchParticipant matchParticipant;

    @Column(nullable = false, length = 128)
    private String puuid;

    @Column(nullable = false)
    private Integer teamId;

    @Column(nullable = false, length = 100)
    private String championName;

    // ---- métricas brutas ----
    private Double kda;
    private Double dmgPerMin;
    private Double goldPerMin;
    private Double csPerMin;
    private Double kp;
    private Double dmgTakenPerMin;
    private Double deathsPerMin;
    private Double xpPerMin;
    private Double visionPerMin;
    private Double ccPerMin;

    // ---- scores normalizados 0–100 ----
    private Double scoreKda;
    private Double scoreDmgPerMin;
    private Double scoreGoldPerMin;
    private Double scoreCsPerMin;
    private Double scoreKp;
    private Double scoreDmgTakenPerMin;
    private Double scoreDeathsPerMin;
    private Double scoreXpPerMin;
    private Double scoreVisionPerMin;
    private Double scoreCcPerMin;

    // ---- score final ----
    private Double finalScore;

}

