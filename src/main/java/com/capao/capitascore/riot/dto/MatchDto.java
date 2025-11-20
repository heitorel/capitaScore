package com.capao.capitascore.riot.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;
import lombok.Setter;

@JsonIgnoreProperties(ignoreUnknown = true)
@Getter
@Setter
public class MatchDto {

    private MatchMetadataDto metadata;
    private MatchInfoDto info;

}

