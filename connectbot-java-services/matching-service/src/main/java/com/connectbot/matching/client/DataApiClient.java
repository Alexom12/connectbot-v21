package com.connectbot.matching.client;

import com.connectbot.matching.dto.dataapi.DataApiEmployeesResponseDTO;
import com.connectbot.matching.dto.MatchingRequestDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.beans.factory.annotation.Autowired;
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
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.charset.StandardCharsets;

@Component
public class DataApiClient {

    private static final Logger logger = LoggerFactory.getLogger(DataApiClient.class);

    private final RestTemplate restTemplate;
    private final String baseUrl;
    private final String serviceToken;
    private final int maxAttempts;
    private final long baseBackoffMs;
    private final ObjectMapper objectMapper;

    @Autowired
    public DataApiClient(RestTemplate restTemplate,
            ObjectMapper objectMapper,
            @Value("${dataapi.base-url:http://web:8000}") String baseUrl,
            @Value("${dataapi.service-token:}") String serviceToken,
            @Value("${dataapi.retry.attempts:3}") int maxAttempts,
            @Value("${dataapi.retry.backoff-ms:200}") long baseBackoffMs) {
        this.restTemplate = restTemplate;
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        // If serviceToken is empty, attempt to read from a secrets file (Docker
        // secrets)
        String token = serviceToken;
        if (token == null || token.isEmpty()) {
            String tokenFile = System.getenv().getOrDefault("DATAAPI_SERVICE_TOKEN_FILE",
                    "/run/secrets/service_auth_token");
            try {
                if (Files.exists(Paths.get(tokenFile))) {
                    byte[] bytes = Files.readAllBytes(Paths.get(tokenFile));
                    token = new String(bytes, StandardCharsets.UTF_8);
                    // normalize: strip BOM and newlines, then trim
                    token = token.replace("\uFEFF", "").replace("\r", "").replace("\n", "").trim();
                    logger.info("Loaded Data API service token from file {}", tokenFile);
                    logger.info("DataApiClient loaded service token mask={} len={}", maskToken(token), token.length());
                }
            } catch (IOException e) {
                logger.debug("Service token file not available at {}: {}", tokenFile, e.getMessage());
            }
        }
        this.serviceToken = token;
        this.maxAttempts = maxAttempts;
        this.baseBackoffMs = baseBackoffMs;
        this.objectMapper = objectMapper;
    }

    /**
     * Compatibility constructor used by tests when an ObjectMapper bean is not
     * provided.
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
            // ensure token is normalized before sending
            String tok = serviceToken.replace("\uFEFF", "").replace("\r", "").replace("\n", "").trim();
            logger.info("Setting Authorization header token_mask={} token_len={}", maskToken(tok), tok.length());
            headers.set("Authorization", "Service " + tok);
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

    private static String maskToken(String s) {
        if (s == null || s.isEmpty())
            return "<empty>";
        if (s.length() <= 8)
            return s + " len=" + s.length();
        return s.substring(0, 8) + "...";
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
