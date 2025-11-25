package com.capao.capitascore.domain.entity;


import com.capao.capitascore.common.BaseEntity;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(
        name = "member_ranking_metrics",
        uniqueConstraints = {
                @UniqueConstraint(
                        name = "uk_mrm_member",
                        columnNames = {"member_id"}
                )
        },
        indexes = {
                @Index(name = "idx_mrm_member", columnList = "member_id"),
                @Index(name = "idx_mrm_puuid", columnList = "puuid")
        }
)
@Getter
@Setter
public class MemberRankingMetrics extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "member_id", nullable = false)
    private Member member;

    @Column(nullable = false, length = 128)
    private String puuid;

    @Column(nullable = false, length = 100)
    private String nick;

    // quantidade de partidas computadas
    @Column(name = "matches_count", nullable = false)
    private Integer matchesCount;

    // média do finalScore
    @Column(name = "mean_final_score", nullable = false)
    private Double meanFinalScore;

    // posição no ranking (1 = melhor)
    @Column(nullable = false)
    private Integer position;

    @Column(nullable = true)
    private String tag;
}

