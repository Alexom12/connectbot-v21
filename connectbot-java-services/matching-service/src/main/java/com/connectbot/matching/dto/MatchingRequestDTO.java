package com.connectbot.matching.dto;

import java.util.List;

/**
 * DTO для запроса на запуск алгоритма подбора.
 */
public class MatchingRequestDTO {

    private List<EmployeeDTO> employees;

    // Getters and Setters

    public List<EmployeeDTO> getEmployees() {
        return employees;
    }

    public void setEmployees(List<EmployeeDTO> employees) {
        this.employees = employees;
    }
}
