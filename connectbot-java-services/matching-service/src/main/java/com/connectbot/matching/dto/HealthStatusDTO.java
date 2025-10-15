package com.connectbot.matching.dto;

/**
 * DTO для статуса здоровья сервиса.
 */
public class HealthStatusDTO {

    private String status;

    public HealthStatusDTO(String status) {
        this.status = status;
    }

    // Getters and Setters

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}
