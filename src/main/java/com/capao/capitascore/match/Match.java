package com.capao.capitascore.match;

import com.capao.capitascore.common.BaseEntity;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "matches")
@Getter
@Setter
public class Match extends BaseEntity {

    @Column(nullable = false, unique = true)
    private String matchId;      // "BR1_3167775457"

    private Long gameId;
    private Long gameCreation;   // timestamp Riot
    private Long gameDuration;   // em segundos
    private Long gameEndTimestamp;
    private String gameMode;
    private String gameType;
    private String gameVersion;
    private Integer mapId;

    @OneToMany(mappedBy = "match", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<MatchParticipant> participants = new ArrayList<>();


    public void addParticipant(MatchParticipant p) {
        participants.add(p);
        p.setMatch(this);
    }
}
