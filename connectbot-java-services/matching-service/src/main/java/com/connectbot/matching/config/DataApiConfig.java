package com.connectbot.matching.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Configuration
public class DataApiConfig {

    private static final Logger logger = LoggerFactory.getLogger(DataApiConfig.class);

    @Bean
    public RestTemplate dataApiRestTemplate(RestTemplateBuilder builder,
            @Value("${dataapi.request.timeout-ms:5000}") long timeoutMs,
            @Value("${dataapi.connect.timeout-ms:2000}") long connectMs) {
        logger.info("Configuring Data API RestTemplate with connectTimeout={}ms requestTimeout={}ms", connectMs,
                timeoutMs);
        // Use HttpComponentsClientHttpRequestFactory with buffered request body
        // so the client sets a Content-Length header instead of using
        // chunked Transfer-Encoding. This avoids "Bad request syntax ('2')"
        // errors from the Django development server which does not handle
        // chunked request bodies correctly.
        return builder
                .requestFactory(() -> {
                    HttpComponentsClientHttpRequestFactory f = new HttpComponentsClientHttpRequestFactory();
                    f.setBufferRequestBody(true);
                    return f;
                })
                .setConnectTimeout(Duration.ofMillis(connectMs))
                .setReadTimeout(Duration.ofMillis(timeoutMs))
                .build();
    }
}
