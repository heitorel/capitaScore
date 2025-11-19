package com.capao.capitascore.riot.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;
import lombok.Setter;

@JsonIgnoreProperties(ignoreUnknown = true)
@Getter
@Setter
public class ParticipantDto {

    private String puuid;
    private String riotIdGameName;
    private String riotIdTagline;

    private int participantId;
    private int teamId;
    private String teamPosition;

    private String championName;
    private int championId;

    private boolean win;

    private int kills;
    private int deaths;
    private int assists;

    private int goldEarned;
    private int champLevel;
    private int totalMinionsKilled;
    private int neutralMinionsKilled;
    private int visionScore;
    private int wardsPlaced;
    private int wardsKilled;

    private int totalDamageDealtToChampions;
    private int totalDamageTaken;

    private int item0;
    private int item1;
    private int item2;
    private int item3;
    private int item4;
    private int item5;
    private int item6;

}
