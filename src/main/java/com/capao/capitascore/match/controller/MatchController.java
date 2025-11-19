package com.capao.capitascore.match.controller;

import com.capao.capitascore.match.service.MatchIngestionService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/matches")
public class MatchController {

    private final MatchIngestionService ingestionService;

    public MatchController(MatchIngestionService ingestionService) {
        this.ingestionService = ingestionService;
    }

    @PostMapping("/sync/by-puuid/{puuid}")
    public ResponseEntity<Void> syncMatches(
            @PathVariable String puuid,
            @RequestParam(defaultValue = "0") int start,
            @RequestParam(defaultValue = "20") int count) {

        ingestionService.syncMatchesForPuuid(puuid, start, count);
        return ResponseEntity.accepted().build();
    }
}
