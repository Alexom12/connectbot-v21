package com.connectbot.matching.dto.dataapi;

import com.connectbot.matching.dto.EmployeeDTO;
import java.util.List;

public class DataApiEmployeesResponseDTO {
    private List<EmployeeDTO> employees;
    private String generated_at;

    public List<EmployeeDTO> getEmployees() {
        return employees;
    }

    public void setEmployees(List<EmployeeDTO> employees) {
        this.employees = employees;
    }

    public String getGenerated_at() {
        return generated_at;
    }

    public void setGenerated_at(String generated_at) {
        this.generated_at = generated_at;
    }
}
