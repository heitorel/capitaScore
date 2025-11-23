package com.capao.capitascore.domain.repository;

import com.capao.capitascore.domain.entity.MatchParticipant;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MatchParticipantRepository extends JpaRepository<MatchParticipant, Long> {
    // ex: buscar histórico de um player
}
