package com.capao.capitascore.controller;

import com.capao.capitascore.domain.service.MatchIngestionService;
import com.capao.capitascore.domain.entity.Member;
import com.capao.capitascore.domain.repository.MemberRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/matches")
public class MatchController {

    private final MatchIngestionService ingestionService;
    private final MemberRepository memberRepository;

    public MatchController(MatchIngestionService ingestionService,
                           MemberRepository memberRepository) {
        this.ingestionService = ingestionService;
        this.memberRepository = memberRepository;
    }

    @PostMapping("/sync/all")
    public ResponseEntity<Void> syncAllMembers(
            @RequestParam(defaultValue = "0") int start,
            @RequestParam(defaultValue = "20") int count) {

        List<Member> members = memberRepository.findAll();

        for (Member m : members) {
            if (m.getActive() == null || Boolean.TRUE.equals(m.getActive())) {
                ingestionService.syncMatchesForPuuid(m.getPuuid(), start, count);
                try {
                    Thread.sleep(3000); // 3s entre cada chamada para evitar rate limit
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break; // opcional: parar se a thread foi interrompida
                }
            }
        }

        return ResponseEntity.accepted().build();
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
