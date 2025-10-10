package com.connectbot.matching.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.List;

/**
 * Модель сотрудника для алгоритмов matching
 * 
 * @author ConnectBot Team  
 * @version 1.0.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Employee {
    
    @NotNull(message = "ID сотрудника обязателен")
    @JsonProperty("id")
    private Long id;
    
    @NotBlank(message = "ФИО сотрудника обязательно")
    @JsonProperty("full_name")
    private String fullName;
    
    @JsonProperty("position")
    private String position;
    
    @JsonProperty("department")
    private String department;
    
    @JsonProperty("business_center")
    private String businessCenter;
    
    @JsonProperty("telegram_id")
    private Long telegramId;
    
    @JsonProperty("telegram_username")
    private String telegramUsername;
    
    @JsonProperty("interests")
    private List<String> interests;
    
    @JsonProperty("is_active")
    private Boolean isActive = true;
    
    /**
     * Проверка активности сотрудника
     */
    public boolean isActiveEmployee() {
        return isActive != null && isActive;
    }
    
    /**
     * Получение отображаемого имени
     */
    public String getDisplayName() {
        if (fullName != null && !fullName.trim().isEmpty()) {
            return fullName.trim();
        }
        return "Сотрудник #" + (id != null ? id : "Unknown");
    }
    
    /**
     * Проверка наличия интересов
     */
    public boolean hasInterests() {
        return interests != null && !interests.isEmpty();
    }
    
    /**
     * Проверка конкретного интереса
     */
    public boolean hasInterest(String interest) {
        return interests != null && interests.contains(interest);
    }
}