package com.capao.capitascore.match;

import com.capao.capitascore.common.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "match_timelines")
@Getter @Setter
public class MatchTimeline extends BaseEntity {

    @Column(nullable = false, unique = true)
    private String matchId;

    @Lob
    @Column(columnDefinition = "LONGTEXT")
    private String rawJson;
}
