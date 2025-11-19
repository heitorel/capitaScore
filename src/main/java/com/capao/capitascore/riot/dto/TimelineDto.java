package com.capao.capitascore.riot.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;
import lombok.Setter;

@JsonIgnoreProperties(ignoreUnknown = true)
@Getter
@Setter
public class TimelineDto {

    private TimelineMetadataDto metadata;
    private TimelineInfoDto info;

}

@JsonIgnoreProperties(ignoreUnknown = true)
@Getter
@Setter
class TimelineMetadataDto {
    private String dataVersion;
    private String matchId;

}

@JsonIgnoreProperties(ignoreUnknown = true)
@Getter
@Setter
class TimelineInfoDto {
    private String endOfGameResult;
    private long frameInterval;
}