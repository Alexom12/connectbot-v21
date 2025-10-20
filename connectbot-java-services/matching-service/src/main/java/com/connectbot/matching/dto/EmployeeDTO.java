package com.connectbot.matching.dto;

import java.util.List;

/**
 * DTO для сотрудника, участвующего в подборе.
 * Содержит только данные, необходимые для алгоритма.
 */
public class EmployeeDTO {

    private Long id;
    private String displayName;
    private String department;
    private List<String> interests;
    private boolean activeEmployee;
    private String position;
    private String businessCode;
    private Long employeeNumber;
    private String username;
    private Grade grade;
    private List<Long> excluded_partners;
    private EmployeePreferencesDTO preferences;

    public enum Grade {
        JUNIOR, MIDDLE, SENIOR, LEAD
    }

    // Getters and Setters

    public boolean isActiveEmployee() {
        return activeEmployee;
    }

    public void setActiveEmployee(boolean activeEmployee) {
        this.activeEmployee = activeEmployee;
    }

    public String getPosition() {
        return position;
    }

    public void setPosition(String position) {
        this.position = position;
    }

    public String getBusinessCode() {
        return businessCode;
    }

    public void setBusinessCode(String businessCode) {
        this.businessCode = businessCode;
    }

    public Long getEmployeeNumber() {
        return employeeNumber;
    }

    public void setEmployeeNumber(Long employeeNumber) {
        this.employeeNumber = employeeNumber;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getDisplayName() {
        return displayName;
    }

    public void setDisplayName(String displayName) {
        this.displayName = displayName;
    }

    public String getDepartment() {
        return department;
    }

    public void setDepartment(String department) {
        this.department = department;
    }

    public List<String> getInterests() {
        return interests;
    }

    public void setInterests(List<String> interests) {
        this.interests = interests;
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
