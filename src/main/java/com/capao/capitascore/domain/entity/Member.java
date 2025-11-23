package com.capao.capitascore.domain.entity;

import com.capao.capitascore.common.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "members")
@Getter
@Setter
public class Member extends BaseEntity {

    @Column(nullable = false)
    private String nome;     // "membro" no JSON

    @Column(nullable = false)
    private String nick;

    @Column(nullable = false)
    private String tag;

    @Column(nullable = false, unique = true, length = 128)
    private String puuid;

    private Boolean active = true;
}
