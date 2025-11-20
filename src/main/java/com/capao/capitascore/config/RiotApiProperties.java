package com.capao.capitascore.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "riot")
@Getter
@Setter
public class RiotApiProperties {

    private String apiKey;
    private String region;
    private String americasBaseUrl;
    private String matchBasePath;
}
