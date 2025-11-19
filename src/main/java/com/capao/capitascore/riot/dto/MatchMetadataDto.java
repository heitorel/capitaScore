package com.capao.capitascore.riot.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
@Getter
@Setter
public class MatchMetadataDto {
    private String dataVersion;
    private String matchId;
    private List<String> participants;

}
