package com.connectbot.matching.dto;

import java.util.List;
import java.util.Map;

/**
 * DTO для ответа с результатами подбора.
 */
public class MatchingResponseDTO {

    private String requestId;
    private String status;
    private String error;
    private String algorithm;
    private List<EmployeePairDTO> pairs;
    private Map<String, Object> meta;

    public MatchingResponseDTO(String requestId, String status, String error, List<EmployeePairDTO> pairs, Map<String, Object> meta) {
        this.requestId = requestId;
        this.status = status;
        this.error = error;
        this.pairs = pairs;
        this.meta = meta;
    }

    // Getters and Setters

    public String getRequestId() {
        return requestId;
    }

    public void setRequestId(String requestId) {
        this.requestId = requestId;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getError() {
        return error;
    }

    public void setError(String error) {
        this.error = error;
    }

    public String getAlgorithm() {
        return algorithm;
    }

    public void setAlgorithm(String algorithm) {
        this.algorithm = algorithm;
    }

    public List<EmployeePairDTO> getPairs() {
        return pairs;
    }

    public void setPairs(List<EmployeePairDTO> pairs) {
        this.pairs = pairs;
    }

    public Map<String, Object> getMeta() {
        return meta;
    }

    public void setMeta(Map<String, Object> meta) {
        this.meta = meta;
    }
}
