package com.connectbot.matching.dto;

/**
 * DTO для предпочтений сотрудника.
 */
public class EmployeePreferencesDTO {

    private boolean with_newcomers;

    // Getters and Setters

    public boolean isWith_newcomers() {
        return with_newcomers;
    }

    public void setWith_newcomers(boolean with_newcomers) {
        this.with_newcomers = with_newcomers;
    }
}
