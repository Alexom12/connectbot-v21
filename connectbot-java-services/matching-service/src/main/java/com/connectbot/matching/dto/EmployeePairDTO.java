package com.connectbot.matching.dto;

/**
 * DTO для пары сотрудников.
 */
public class EmployeePairDTO {

    private Long employee1_id;
    private Long employee2_id;

    public EmployeePairDTO(Long employee1_id, Long employee2_id) {
        this.employee1_id = employee1_id;
        this.employee2_id = employee2_id;
    }

    // Getters and Setters

    public Long getEmployee1_id() {
        return employee1_id;
    }

    public void setEmployee1_id(Long employee1_id) {
        this.employee1_id = employee1_id;
    }

    public Long getEmployee2_id() {
        return employee2_id;
    }

    public void setEmployee2_id(Long employee2_id) {
        this.employee2_id = employee2_id;
    }
}
