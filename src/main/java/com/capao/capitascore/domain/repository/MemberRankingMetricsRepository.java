package com.capao.capitascore.domain.repository;

import com.capao.capitascore.domain.entity.MemberRankingMetrics;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface MemberRankingMetricsRepository extends JpaRepository<MemberRankingMetrics, Long> {

    List<MemberRankingMetrics> findAllByOrderByPositionAsc();
}
