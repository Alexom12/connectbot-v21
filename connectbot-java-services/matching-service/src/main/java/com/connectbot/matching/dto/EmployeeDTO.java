package com.connectbot.matching.dto;

import java.util.List;

/**
 * DTO для сотрудника, участвующего в подборе.
 * Содержит только данные, необходимые для алгоритма.
 */
public class EmployeeDTO {

    private Long id;
    private String department;
    private Grade grade;
    private List<Long> excluded_partners;
    private EmployeePreferencesDTO preferences;

    public enum Grade {
        JUNIOR, MIDDLE, SENIOR, LEAD
    }

    // Getters and Setters

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getDepartment() {
        return department;
    }

    public void setDepartment(String department) {
        this.department = department;
    }

    public Grade getGrade() {
        return grade;
    }

    public void setGrade(Grade grade) {
        this.grade = grade;
    }

    public List<Long> getExcluded_partners() {
        return excluded_partners;
    }

    public void setExcluded_partners(List<Long> excluded_partners) {
        this.excluded_partners = excluded_partners;
    }

    public EmployeePreferencesDTO getPreferences() {
        return preferences;
    }

    public void setPreferences(EmployeePreferencesDTO preferences) {
        this.preferences = preferences;
    }
}
