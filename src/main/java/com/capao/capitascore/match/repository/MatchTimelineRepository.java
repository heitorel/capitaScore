package com.capao.capitascore.match.repository;

import com.capao.capitascore.match.MatchTimeline;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface MatchTimelineRepository extends JpaRepository<MatchTimeline, Long> {
    Optional<MatchTimeline> findByMatchId(String matchId);
}
