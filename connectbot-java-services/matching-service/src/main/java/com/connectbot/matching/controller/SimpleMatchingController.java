package com.connectbot.matching.controller;

import com.connectbot.matching.model.Employee;
import com.connectbot.matching.model.MatchingResult;
import com.connectbot.matching.service.MatchingService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * REST контроллер для алгоритмов простого matching
 * 
 * @author ConnectBot Team
 * @version 1.0.0
 */
@RestController
@RequestMapping("/api/matching")
@Validated
@CrossOrigin(origins = "*")
public class SimpleMatchingController {
    
    private static final Logger logger = LoggerFactory.getLogger(SimpleMatchingController.class);
    
    @Autowired
    private MatchingService matchingService;
    
    /**
     * Простой алгоритм matching для кофе
     * 
     * @param employees список сотрудников в JSON формате
     * @return результат matching с парами
     */
    @PostMapping("/coffee/simple")
    public ResponseEntity<MatchingResult> simpleMatching(@Valid @RequestBody List<Employee> employees) {
        logger.info("Получен запрос на простой matching для {} сотрудников", 
            employees != null ? employees.size() : 0);
        
        try {
            MatchingResult result = matchingService.simpleRandomMatching(employees);
            
            logger.info("Простой matching выполнен успешно: {} пар создано", result.getTotalPairs());
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Ошибка при выполнении простого matching: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
    
    /**
     * Matching для кофе с учетом интересов
     * 
     * @param employees список сотрудников
     * @param interest конкретный интерес для фильтрации
     * @return результат matching
     */
    @PostMapping("/coffee/interest")
    public ResponseEntity<MatchingResult> interestBasedMatching(
            @Valid @RequestBody List<Employee> employees,
            @RequestParam(name = "interest", defaultValue = "coffee") String interest) {
        
        logger.info("Получен запрос на interest-based matching для интереса '{}' и {} сотрудников", 
            interest, employees != null ? employees.size() : 0);
        
        try {
            MatchingResult result = matchingService.interestBasedMatching(employees, interest);
            
            logger.info("Interest-based matching выполнен успешно: {} пар создано", result.getTotalPairs());
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Ошибка при выполнении interest-based matching: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
    
    /**
     * Matching с избеганием коллег из одного отдела
     * 
     * @param employees список сотрудников
     * @return результат matching
     */
    @PostMapping("/coffee/cross-department")
    public ResponseEntity<MatchingResult> crossDepartmentMatching(@Valid @RequestBody List<Employee> employees) {
        logger.info("Получен запрос на cross-department matching для {} сотрудников", 
            employees != null ? employees.size() : 0);
        
        try {
            MatchingResult result = matchingService.crossDepartmentMatching(employees);
            
            logger.info("Cross-department matching выполнен успешно: {} пар создано", result.getTotalPairs());
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            logger.error("Ошибка при выполнении cross-department matching: {}", e.getMessage(), e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
    
    /**
     * Получение информации о доступных алгоритмах matching
     * 
     * @return список доступных алгоритмов
     */
    @GetMapping("/algorithms")
    public ResponseEntity<Map<String, Object>> getAvailableAlgorithms() {
        logger.debug("Запрос списка доступных алгоритмов");
        
        Map<String, Object> algorithms = new HashMap<>();
        
        algorithms.put("simple", Map.of(
            "name", "Простой случайный matching",
            "description", "Случайное перемешивание и создание пар",
            "endpoint", "/api/matching/coffee/simple",
            "method", "POST"
        ));
        
        algorithms.put("interest_based", Map.of(
            "name", "Matching по интересам",
            "description", "Создание пар среди сотрудников с общими интересами",
            "endpoint", "/api/matching/coffee/interest",
            "method", "POST"
        ));
        
        algorithms.put("cross_department", Map.of(
            "name", "Межотдельческий matching",
            "description", "Создание пар из разных отделов",
            "endpoint", "/api/matching/coffee/cross-department",
            "method", "POST"
        ));
        
        return ResponseEntity.ok(Map.of(
            "algorithms", algorithms,
            "total", algorithms.size(),
            "version", "1.0.0"
        ));
    }
}