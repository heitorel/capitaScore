package com.capao.capitascore.controller;

import com.capao.capitascore.domain.dto.PlayerRankingDto;
import com.capao.capitascore.domain.repository.PlayerMatchMetricsRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/ranking")
public class RankingController {

    private final PlayerMatchMetricsRepository metricsRepository;

    public RankingController(PlayerMatchMetricsRepository metricsRepository) {
        this.metricsRepository = metricsRepository;
    }

    /**
     * Ranking geral por jogador, ordenado por média de finalScore (desc).
     *
     * Exemplo:
     * GET /api/ranking?minGames=5
     */
    @GetMapping
    public ResponseEntity<List<PlayerRankingDto>> getRanking(
            @RequestParam(name = "minGames", defaultValue = "3") long minGames) {

        List<PlayerRankingDto> ranking = metricsRepository.findRankingByAvgFinalScore(minGames);
        return ResponseEntity.ok(ranking);
    }
}
