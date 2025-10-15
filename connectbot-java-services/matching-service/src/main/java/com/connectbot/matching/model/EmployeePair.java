package com.connectbot.matching.model;

/**
 * Минимальная модель пары сотрудников.
 */
public class EmployeePair {
    private Employee employee1;
    private Employee employee2;

    public EmployeePair() {
    }

    public EmployeePair(Employee e1, Employee e2) {
        this.employee1 = e1;
        this.employee2 = e2;
    }

    public Employee getEmployee1() {
        return employee1;
    }

    public void setEmployee1(Employee employee1) {
        this.employee1 = employee1;
    }

    public Employee getEmployee2() {
        return employee2;
    }

    public void setEmployee2(Employee employee2) {
        this.employee2 = employee2;
    }

    // Пара считается валидной, если оба сотрудника не null и имеют разные id
    public boolean isValid() {
        if (employee1 == null || employee2 == null)
            return false;
        if (employee1.getId() == null || employee2.getId() == null)
            return false;
        return !employee1.getId().equals(employee2.getId());
    }
}
