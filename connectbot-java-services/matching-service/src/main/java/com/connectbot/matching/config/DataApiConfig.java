package com.connectbot.matching.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Configuration
public class DataApiConfig {

    private static final Logger logger = LoggerFactory.getLogger(DataApiConfig.class);

    @Bean
    public RestTemplate dataApiRestTemplate(RestTemplateBuilder builder,
                                            @Value("${dataapi.request.timeout-ms:5000}") long timeoutMs,
                                            @Value("${dataapi.connect.timeout-ms:2000}") long connectMs) {
        logger.info("Configuring Data API RestTemplate with connectTimeout={}ms requestTimeout={}ms", connectMs, timeoutMs);
        return builder
                .setConnectTimeout(Duration.ofMillis(connectMs))
                .setReadTimeout(Duration.ofMillis(timeoutMs))
                .build();
    }
}
