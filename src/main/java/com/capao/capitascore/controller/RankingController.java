package com.capao.capitascore.controller;

import com.capao.capitascore.domain.dto.MemberRankingDto;
import com.capao.capitascore.domain.entity.MemberRankingMetrics;
import com.capao.capitascore.domain.repository.MemberRankingMetricsRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/ranking")
public class RankingController {

    private final MemberRankingMetricsRepository rankingRepository;

    public RankingController(MemberRankingMetricsRepository rankingRepository) {
        this.rankingRepository = rankingRepository;
    }
    @GetMapping
    public ResponseEntity<List<MemberRankingDto>> getRanking(
            @RequestParam(name = "minGames", defaultValue = "0") int minGames) {

        List<MemberRankingMetrics> entities = rankingRepository.findAllByOrderByPositionAsc();

        List<MemberRankingDto> response = entities.stream()
                .filter(e -> e.getMatchesCount() != null && e.getMatchesCount() >= minGames)
                .map(e -> new MemberRankingDto(
                        e.getPosition(),
                        e.getNick(),
                        e.getPuuid(),
                        e.getMatchesCount(),
                        e.getMeanFinalScore()
                ))
                .toList();

        return ResponseEntity.ok(response);
    }
}
