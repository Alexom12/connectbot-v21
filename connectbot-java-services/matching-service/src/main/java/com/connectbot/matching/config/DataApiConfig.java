package com.connectbot.matching.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

import org.apache.hc.client5.http.config.RequestConfig;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.util.Timeout;

import java.time.Duration;

@Configuration
public class DataApiConfig {

    private static final Logger logger = LoggerFactory.getLogger(DataApiConfig.class);

    @Bean
    public RestTemplate dataApiRestTemplate(
        @Value("${dataapi.request.timeout-ms:5000}") long timeoutMs,
        @Value("${dataapi.connect.timeout-ms:2000}") long connectMs) {
    logger.info("Configuring Data API RestTemplate with connectTimeout={}ms requestTimeout={}ms", connectMs,
        timeoutMs);

    // Build an Apache HttpClient5 instance with explicit timeouts configured
    // so we can control connect/response timeouts without relying on
    // RestTemplateBuilder's reflective configuration which expects
    // different setter methods on the factory.
    RequestConfig requestConfig = RequestConfig.custom()
        .setConnectTimeout(Timeout.ofMilliseconds(connectMs))
        .setResponseTimeout(Timeout.ofMilliseconds(timeoutMs))
        .build();

    CloseableHttpClient httpClient = HttpClients.custom()
        .setDefaultRequestConfig(requestConfig)
        .build();

    HttpComponentsClientHttpRequestFactory f = new HttpComponentsClientHttpRequestFactory(httpClient);
    f.setBufferRequestBody(true);

    return new RestTemplate(f);
    }
}
