package com.connectbot.matching.client;

import com.connectbot.matching.dto.dataapi.DataApiEmployeesResponseDTO;
import com.connectbot.matching.dto.MatchingRequestDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

@Component
public class DataApiClient {

    private static final Logger logger = LoggerFactory.getLogger(DataApiClient.class);

    private final RestTemplate restTemplate;
    private final String baseUrl;
    private final String serviceToken;
    private final int maxAttempts;
    private final long baseBackoffMs;
    private final ObjectMapper objectMapper;

    public DataApiClient(RestTemplate restTemplate,
            ObjectMapper objectMapper,
            @Value("${dataapi.base-url:http://web:8000}") String baseUrl,
            @Value("${dataapi.service-token:}") String serviceToken,
            @Value("${dataapi.retry.attempts:3}") int maxAttempts,
            @Value("${dataapi.retry.backoff-ms:200}") long baseBackoffMs) {
        this.restTemplate = restTemplate;
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.serviceToken = serviceToken;
        this.maxAttempts = maxAttempts;
        this.baseBackoffMs = baseBackoffMs;
        this.objectMapper = objectMapper;
    }

    /**
     * Compatibility constructor used by tests when an ObjectMapper bean is not provided.
     */
    public DataApiClient(RestTemplate restTemplate,
                         String baseUrl,
                         String serviceToken,
                         int maxAttempts,
                         int baseBackoffMs) {
        this(restTemplate, new ObjectMapper(), baseUrl, serviceToken, maxAttempts, (long) baseBackoffMs);
    }

    public DataApiEmployeesResponseDTO getEmployeesForMatching(Map<String, Object> body) throws RestClientException {
        String url = baseUrl + "/api/v1/data/employees-for-matching";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        if (serviceToken != null && !serviceToken.isEmpty()) {
            headers.set("Authorization", "Service " + serviceToken);
        }
        String jsonBody;
        try {
            jsonBody = objectMapper.writeValueAsString(body);
            headers.setContentLength(jsonBody.length());
            logger.info("DataApiClient sending payload length={} chars: {}", jsonBody.length(),
                    jsonBody.length() > 200 ? jsonBody.substring(0, 200) + "..." : jsonBody);
        } catch (JsonProcessingException e) {
            logger.warn("Failed to serialize Data API payload: {}", e.getMessage());
            throw new DataApiException("Failed to serialize request body");
        }

        HttpEntity<String> entity = new HttpEntity<>(jsonBody, headers);

        int attempt = 0;
        while (true) {
            attempt++;
            try {
                ResponseEntity<DataApiEmployeesResponseDTO> resp = restTemplate.exchange(url, HttpMethod.POST, entity,
                        DataApiEmployeesResponseDTO.class);
                if (!resp.getStatusCode().is2xxSuccessful()) {
                    throw new DataApiException("Non-2xx response from Data API: " + resp.getStatusCodeValue(),
                            resp.getStatusCodeValue());
                }
                return resp.getBody();
            } catch (RestClientException ex) {
                logger.warn("DataApiClient attempt {} failed: {}", attempt, ex.getMessage());
                if (attempt >= maxAttempts) {
                    logger.error("DataApiClient exhausted retries, throwing DataApiException");
                    throw new DataApiException("Failed to call Data API after retries: " + ex.getMessage());
                }
                try {
                    long backoff = baseBackoffMs * (1L << (attempt - 1));
                    Thread.sleep(backoff);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new DataApiException("Interrupted during backoff");
                }
            }
        }
    }

    public boolean healthCheck() {
        String url = baseUrl + "/api/v1/data/health";
        HttpHeaders headers = new HttpHeaders();
        if (serviceToken != null && !serviceToken.isEmpty()) {
            headers.set("Authorization", "Service " + serviceToken);
        }
        HttpEntity<Void> entity = new HttpEntity<>(headers);
        try {
            ResponseEntity<String> r = restTemplate.exchange(url, HttpMethod.GET, entity, String.class);
            return r.getStatusCode().is2xxSuccessful();
        } catch (Exception ex) {
            logger.warn("DataApiClient health check failed: {}", ex.getMessage());
            return false;
        }
    }
}
