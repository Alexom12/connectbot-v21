package com.connectbot.matching.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Результат алгоритма matching
 * 
 * @author ConnectBot Team
 * @version 1.0.0
 */
@Data
@NoArgsConstructor  
@AllArgsConstructor
public class MatchingResult {
    
    @JsonProperty("pairs")
    private List<EmployeePair> pairs;
    
    @JsonProperty("unmatched")
    private List<Employee> unmatched;
    
    @JsonProperty("algorithm")
    private String algorithm;
    
    @JsonProperty("total_employees")
    private Integer totalEmployees;
    
    @JsonProperty("total_pairs")
    private Integer totalPairs;
    
    @JsonProperty("success_rate")
    private Double successRate;
    
    @JsonProperty("created_at")
    private LocalDateTime createdAt;
    
    /**
     * Конструктор с автоматическим расчетом статистики
     */
    public MatchingResult(List<EmployeePair> pairs, List<Employee> unmatched, String algorithm) {
        this.pairs = pairs;
        this.unmatched = unmatched;
        this.algorithm = algorithm;
        this.totalPairs = pairs != null ? pairs.size() : 0;
        this.totalEmployees = (totalPairs * 2) + (unmatched != null ? unmatched.size() : 0);
        this.successRate = totalEmployees > 0 ? (double)(totalPairs * 2) / totalEmployees * 100 : 0.0;
        this.createdAt = LocalDateTime.now();
    }
    
    /**
     * Проверка успешности matching
     */
    public boolean isSuccessful() {
        return pairs != null && !pairs.isEmpty();
    }
    
    /**
     * Получение количества участников в парах
     */
    public int getMatchedCount() {
        return totalPairs * 2;
    }
}