package com.capao.capitascore.domain.repository;

import com.capao.capitascore.domain.entity.Match;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface MatchRepository extends JpaRepository<Match, Long> {
    Optional<Match> findByMatchId(String matchId);
}
