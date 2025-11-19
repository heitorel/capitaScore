package com.capao.capitascore.match.controller;

import com.capao.capitascore.match.service.MatchIngestionService;
import com.capao.capitascore.member.Member;
import com.capao.capitascore.member.MemberRepository;
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
            @RequestParam(defaultValue = "6") int count) {

        List<Member> members = memberRepository.findAll();

        members.stream()
                .filter(m -> m.getActive() == null || Boolean.TRUE.equals(m.getActive()))
                .forEach(m -> ingestionService.syncMatchesForPuuid(m.getPuuid(), start, count));

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
