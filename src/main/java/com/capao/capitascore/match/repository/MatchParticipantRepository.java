package com.capao.capitascore.match.repository;

import com.capao.capitascore.match.MatchParticipant;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MatchParticipantRepository extends JpaRepository<MatchParticipant, Long> {
    // ex: buscar histórico de um player
}
