package com.capao.capitascore.domain.repository;

import com.capao.capitascore.domain.entity.Member;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface MemberRepository extends JpaRepository<Member, Long> {
    Optional<Member> findByPuuid(String puuid);
}
