package com.capao.capitascore.metrics.players.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class PlayerRankingDto {

    private String puuid;
    private String nome;           // pode ser null se não tiver member
    private String nick;           // idem
    private Double avgFinalScore;
    private Long gamesPlayed;

}

