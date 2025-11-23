package com.capao.capitascore.domain.repository;

import com.capao.capitascore.domain.entity.PlayerMatchMetrics;
import com.capao.capitascore.domain.dto.PlayerRankingDto;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;

public interface PlayerMatchMetricsRepository extends JpaRepository<PlayerMatchMetrics, Long> {

    Optional<PlayerMatchMetrics> findByMatchIdAndMatchParticipantId(Long matchId, Long matchParticipantId);

    List<PlayerMatchMetrics> findByPuuid(String puuid);

    @Query("""
        SELECT new com.capao.capitascore.domain.dto.PlayerRankingDto(
            pmm.puuid,
            COALESCE(m.nome, 'Desconhecido'),
            COALESCE(m.nick, ''),
            AVG(pmm.finalScore),
            COUNT(pmm.id)
        )
        FROM PlayerMatchMetrics pmm
        JOIN pmm.matchParticipant mp
        LEFT JOIN mp.member m
        GROUP BY pmm.puuid, m.nome, m.nick
        HAVING COUNT(pmm.id) >= :minGames
        ORDER BY AVG(pmm.finalScore) DESC
        """)
    List<PlayerRankingDto> findRankingByAvgFinalScore(long minGames);
}
