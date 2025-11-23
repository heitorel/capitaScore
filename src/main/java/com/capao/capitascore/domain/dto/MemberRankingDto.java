package com.capao.capitascore.domain.dto;


import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class MemberRankingDto {

    private Integer position;
    private String nick;
    private String puuid;
    private Integer matches;
    private Double meanFinalScore;

}
