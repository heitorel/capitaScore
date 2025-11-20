package com.capao.capitascore.riot.client;

import com.capao.capitascore.riot.dto.MatchDto;
import com.capao.capitascore.riot.dto.TimelineDto;

import java.util.List;

public interface RiotMatchClient {

    List<String> getMatchIdsByPuuid(String puuid, int start, int count);

    MatchDto getMatchById(String matchId);

    TimelineDto getTimelineByMatchId(String matchId);

    String getRawTimelineJson(String matchId);
}
