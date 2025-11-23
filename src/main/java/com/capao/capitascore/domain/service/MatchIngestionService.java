package com.capao.capitascore.domain.service;

import com.capao.capitascore.domain.entity.Match;
import com.capao.capitascore.domain.entity.MatchParticipant;
import com.capao.capitascore.domain.entity.MatchTimeline;
import com.capao.capitascore.domain.repository.MatchParticipantRepository;
import com.capao.capitascore.domain.repository.MatchRepository;
import com.capao.capitascore.domain.repository.MatchTimelineRepository;
import com.capao.capitascore.domain.repository.MemberRepository;
import com.capao.capitascore.riot.client.RiotMatchClient;
import com.capao.capitascore.riot.dto.MatchDto;
import com.capao.capitascore.riot.dto.MatchInfoDto;
import com.capao.capitascore.riot.dto.ParticipantDto;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class MatchIngestionService {

    private final RiotMatchClient riotMatchClient;
    private final MatchRepository matchRepository;
    private final MatchParticipantRepository matchParticipantRepository;
    private final MatchTimelineRepository matchTimelineRepository;
    private final MemberRepository memberRepository;

    public MatchIngestionService(RiotMatchClient riotMatchClient,
                                 MatchRepository matchRepository,
                                 MatchParticipantRepository matchParticipantRepository,
                                 MatchTimelineRepository matchTimelineRepository,
                                 MemberRepository memberRepository) {
        this.riotMatchClient = riotMatchClient;
        this.matchRepository = matchRepository;
        this.matchParticipantRepository = matchParticipantRepository;
        this.matchTimelineRepository = matchTimelineRepository;
        this.memberRepository = memberRepository;
    }

    @Transactional
    public void syncMatchesForPuuid(String puuid, int start, int count) {
        List<String> matchIds = riotMatchClient.getMatchIdsByPuuid(puuid, start, count);

        for (String matchId : matchIds) {
            if (matchRepository.findByMatchId(matchId).isPresent()) {
                continue; // já temos
            }

            MatchDto matchDto = riotMatchClient.getMatchById(matchId);
            Match match = mapToMatchEntity(matchDto);
            matchRepository.save(match);

            // timeline bruto
            String rawTimeline = riotMatchClient.getRawTimelineJson(matchId);
            MatchTimeline timeline = new MatchTimeline();
            timeline.setMatchId(matchId);
            timeline.setRawJson(rawTimeline);
            matchTimelineRepository.save(timeline);
        }
    }

    private Match mapToMatchEntity(MatchDto dto) {
        MatchInfoDto info = dto.getInfo();

        Match match = new Match();
        match.setMatchId(dto.getMetadata().getMatchId());
        match.setGameId(info.getGameId());
        match.setGameCreation(info.getGameCreation());
        match.setGameDuration(info.getGameDuration());
        match.setGameEndTimestamp(info.getGameEndTimestamp());
        match.setGameMode(info.getGameMode());
        match.setGameType(info.getGameType());
        match.setGameVersion(info.getGameVersion());
        match.setMapId(info.getMapId());

        for (ParticipantDto p : info.getParticipants()) {
            MatchParticipant mp = mapParticipant(p, match);
            match.addParticipant(mp);
        }

        return match;
    }

    private MatchParticipant mapParticipant(ParticipantDto p, Match match) {
        MatchParticipant mp = new MatchParticipant();
        mp.setMatch(match);

        mp.setParticipantNumber(p.getParticipantId());
        mp.setPuuid(p.getPuuid());
        mp.setRiotIdGameName(p.getRiotIdGameName());
        mp.setRiotIdTagline(p.getRiotIdTagline());
        mp.setTeamId(p.getTeamId());
        mp.setTeamPosition(p.getTeamPosition());
        mp.setChampionName(p.getChampionName());
        mp.setChampionId(p.getChampionId());
        mp.setWin(p.isWin());
        mp.setKills(p.getKills());
        mp.setDeaths(p.getDeaths());
        mp.setAssists(p.getAssists());
        mp.setGoldEarned(p.getGoldEarned());
        mp.setChampLevel(p.getChampLevel());
        mp.setTotalMinionsKilled(p.getTotalMinionsKilled());
        mp.setNeutralMinionsKilled(p.getNeutralMinionsKilled());
        mp.setVisionScore(p.getVisionScore());
        mp.setWardsPlaced(p.getWardsPlaced());
        mp.setWardsKilled(p.getWardsKilled());
        mp.setTotalDamageDealtToChampions(p.getTotalDamageDealtToChampions());
        mp.setTotalDamageTaken(p.getTotalDamageTaken());
        mp.setItem0(p.getItem0());
        mp.setItem1(p.getItem1());
        mp.setItem2(p.getItem2());
        mp.setItem3(p.getItem3());
        mp.setItem4(p.getItem4());
        mp.setItem5(p.getItem5());
        mp.setItem6(p.getItem6());

        memberRepository.findByPuuid(p.getPuuid())
                .ifPresent(mp::setMember);

        return mp;
    }
}