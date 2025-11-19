package com.capao.capitascore.match;

import com.capao.capitascore.common.BaseEntity;
import com.capao.capitascore.member.Member;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "match_participants",
        indexes = {
                @Index(name = "idx_mp_match", columnList = "match_id"),
                @Index(name = "idx_mp_puuid", columnList = "puuid")
        })
@Getter
@Setter
public class MatchParticipant extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "match_id", nullable = false)
    private Match match;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "member_id")
    private Member member;   // null se não for do seu grupo

    private Integer participantNumber;  // 1..10
    private String puuid;

    private String riotIdGameName;
    private String riotIdTagline;

    private Integer teamId;          // 100 ou 200
    private String teamPosition;     // TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY

    private String championName;
    private Integer championId;

    private Boolean win;

    private Integer kills;
    private Integer deaths;
    private Integer assists;

    private Integer goldEarned;
    private Integer champLevel;
    private Integer totalMinionsKilled;
    private Integer neutralMinionsKilled;
    private Integer visionScore;
    private Integer wardsPlaced;
    private Integer wardsKilled;

    private Integer totalDamageDealtToChampions;
    private Integer totalDamageTaken;

    private Integer item0;
    private Integer item1;
    private Integer item2;
    private Integer item3;
    private Integer item4;
    private Integer item5;
    private Integer item6;
}
