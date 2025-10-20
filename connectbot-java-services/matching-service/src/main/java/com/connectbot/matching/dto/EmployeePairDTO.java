package com.connectbot.matching.dto;

/**
 * DTO для пары сотрудников.
 */
public class EmployeePairDTO {

    private EmployeeDTO employee1;
    private EmployeeDTO employee2;

    public EmployeePairDTO() {
    }

    public EmployeePairDTO(EmployeeDTO employee1, EmployeeDTO employee2) {
        this.employee1 = employee1;
        this.employee2 = employee2;
    }

    // Getters and Setters

    public EmployeeDTO getEmployee1() {
        return employee1;
    }

    public void setEmployee1(EmployeeDTO employee1) {
        this.employee1 = employee1;
    }

    public EmployeeDTO getEmployee2() {
        return employee2;
    }

    public void setEmployee2(EmployeeDTO employee2) {
        this.employee2 = employee2;
    }
}
