package com.connectbot.matching.model;

import com.connectbot.matching.dto.EmployeeDTO;

import java.util.List;

/**
 * Минимальная модель сотрудника для компиляции сервиса.
 */
public class Employee {

    private Long id;
    private String displayName;
    private String department;
    private boolean activeEmployee = true;
    private List<String> interests;

    public Employee() {
    }

    public Employee(Long id, String displayName) {
        this.id = id;
        this.displayName = displayName;
    }

    // Convenience constructor used in tests and older codepaths
    public Employee(Long id, String displayName, String position, String department, String businessCode,
            Long employeeNumber, String username, List<String> interests, boolean activeEmployee) {
        this.id = id;
        this.displayName = displayName;
        this.position = position;
        this.department = department;
        this.businessCode = businessCode;
        this.employeeNumber = employeeNumber;
        this.username = username;
        this.interests = interests;
        this.activeEmployee = activeEmployee;
    }

    // Additional optional fields to match test expectations
    private String position;
    private String businessCode;
    private Long employeeNumber;
    private String username;

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

    public boolean isActiveEmployee() {
        return activeEmployee;
    }

    public void setActiveEmployee(boolean activeEmployee) {
        this.activeEmployee = activeEmployee;
    }

    public List<String> getInterests() {
        return interests;
    }

    public void setInterests(List<String> interests) {
        this.interests = interests;
    }

    public EmployeeDTO toDTO() {
        EmployeeDTO dto = new EmployeeDTO();
        dto.setId(this.id);
        dto.setDisplayName(this.displayName);
        dto.setDepartment(this.department);
        dto.setInterests(this.interests);
        dto.setActiveEmployee(this.activeEmployee);
        dto.setPosition(this.position);
        dto.setBusinessCode(this.businessCode);
        dto.setEmployeeNumber(this.employeeNumber);
        dto.setUsername(this.username);
        return dto;
    }

    public boolean hasInterest(String interest) {
        return interests != null && interests.contains(interest);
    }
}
