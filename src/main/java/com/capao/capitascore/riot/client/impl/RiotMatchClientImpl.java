package com.capao.capitascore.riot.client.impl;

import com.capao.capitascore.config.RiotApiProperties;
import com.capao.capitascore.riot.client.RiotMatchClient;
import com.capao.capitascore.riot.dto.MatchDto;
import com.capao.capitascore.riot.dto.TimelineDto;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.util.Arrays;
import java.util.List;

@Component
public class RiotMatchClientImpl implements RiotMatchClient {

    private final RestTemplate restTemplate;
    private final RiotApiProperties props;
    private final ObjectMapper objectMapper;

    public RiotMatchClientImpl(RestTemplate restTemplate,
                               RiotApiProperties props,
                               ObjectMapper objectMapper) {
        this.restTemplate = restTemplate;
        this.props = props;
        this.objectMapper = objectMapper;
    }

    private HttpHeaders defaultHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.set("X-Riot-Token", props.getApiKey());
        return headers;
    }

    @Override
    public List<String> getMatchIdsByPuuid(String puuid, int start, int count) {
        String url = UriComponentsBuilder
                .fromHttpUrl(props.getAmericasBaseUrl()
                        + props.getMatchBasePath()
                        + "/matches/by-puuid/{puuid}/ids")
                .queryParam("start", start)
                .queryParam("count", count)
                .buildAndExpand(puuid)
                .toUriString();

        HttpEntity<Void> entity = new HttpEntity<>(defaultHeaders());

        ResponseEntity<String[]> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                entity,
                String[].class
        );

        return Arrays.asList(response.getBody());
    }

    @Override
    public MatchDto getMatchById(String matchId) {
        String url = props.getAmericasBaseUrl()
                + props.getMatchBasePath()
                + "/matches/" + matchId;

        HttpEntity<Void> entity = new HttpEntity<>(defaultHeaders());

        ResponseEntity<MatchDto> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                entity,
                MatchDto.class
        );

        return response.getBody();
    }

    @Override
    public TimelineDto getTimelineByMatchId(String matchId) {
        String url = props.getAmericasBaseUrl()
                + props.getMatchBasePath()
                + "/matches/" + matchId + "/timeline";

        HttpEntity<Void> entity = new HttpEntity<>(defaultHeaders());

        ResponseEntity<TimelineDto> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                entity,
                TimelineDto.class
        );

        return response.getBody();
    }

    @Override
    public String getRawTimelineJson(String matchId) {
        String url = props.getAmericasBaseUrl()
                + props.getMatchBasePath()
                + "/matches/" + matchId + "/timeline";

        HttpEntity<Void> entity = new HttpEntity<>(defaultHeaders());

        ResponseEntity<String> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                entity,
                String.class
        );

        return response.getBody();
    }
}
