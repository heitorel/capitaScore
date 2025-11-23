package com.capao.capitascore.domain.repository;

import com.capao.capitascore.domain.entity.MatchTimeline;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface MatchTimelineRepository extends JpaRepository<MatchTimeline, Long> {
    Optional<MatchTimeline> findByMatchId(String matchId);
}
