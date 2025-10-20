package com.connectbot.matching.dto;

import java.util.List;

/**
 * DTO для запроса на запуск алгоритма подбора.
 */
public class MatchingRequestDTO {

    private String requestId;
    private java.util.Map<String, Object> algorithmParams;
    private List<EmployeeDTO> employees;

    // Getters and Setters

    public String getRequestId() {
        return requestId;
    }

    public void setRequestId(String requestId) {
        this.requestId = requestId;
    }

    public java.util.Map<String, Object> getAlgorithmParams() {
        return algorithmParams;
    }

    public void setAlgorithmParams(java.util.Map<String, Object> algorithmParams) {
        this.algorithmParams = algorithmParams;
    }

    public List<EmployeeDTO> getEmployees() {
        return employees;
    }

    public void setEmployees(List<EmployeeDTO> employees) {
        this.employees = employees;
    }
}
