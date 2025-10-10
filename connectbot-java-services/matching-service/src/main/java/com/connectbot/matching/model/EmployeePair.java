package com.connectbot.matching.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Пара сотрудников для активности
 * 
 * @author ConnectBot Team
 * @version 1.0.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class EmployeePair {
    
    @JsonProperty("employee1")
    private Employee employee1;
    
    @JsonProperty("employee2") 
    private Employee employee2;
    
    @JsonProperty("match_score")
    private Double matchScore;
    
    /**
     * Конструктор без match score
     */
    public EmployeePair(Employee employee1, Employee employee2) {
        this.employee1 = employee1;
        this.employee2 = employee2;
        this.matchScore = 1.0; // По умолчанию
    }
    
    /**
     * Проверка валидности пары
     */
    public boolean isValid() {
        return employee1 != null && employee2 != null && 
               !employee1.getId().equals(employee2.getId());
    }
    
    /**
     * Получение отображаемого названия пары
     */
    public String getDisplayName() {
        String name1 = employee1 != null ? employee1.getDisplayName() : "Unknown";
        String name2 = employee2 != null ? employee2.getDisplayName() : "Unknown";
        return name1 + " & " + name2;
    }
    
    /**
     * Проверка общих интересов
     */
    public boolean hasCommonInterests() {
        if (employee1 == null || employee2 == null || 
            !employee1.hasInterests() || !employee2.hasInterests()) {
            return false;
        }
        
        return employee1.getInterests().stream()
            .anyMatch(interest -> employee2.getInterests().contains(interest));
    }
}