package com.connectbot.matching.service;

import com.connectbot.matching.model.Employee;
import com.connectbot.matching.model.MatchingResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Тесты для MatchingService
 * 
 * @author ConnectBot Team
 * @version 1.0.0
 */
@SpringBootTest
class MatchingServiceTest {
    
    private MatchingService matchingService;
    private List<Employee> testEmployees;
    
    @BeforeEach
    void setUp() {
        matchingService = new MatchingService();
        
        // Создаем тестовых сотрудников
        testEmployees = Arrays.asList(
            new Employee(1L, "Иван Иванов", "Разработчик", "IT", "БЦ1", 123L, "ivan", Arrays.asList("coffee", "chess"), true),
            new Employee(2L, "Петр Петров", "Аналитик", "Analytics", "БЦ1", 124L, "petr", Arrays.asList("coffee", "lunch"), true),
            new Employee(3L, "Мария Сидорова", "Дизайнер", "Design", "БЦ2", 125L, "maria", Arrays.asList("coffee", "photo"), true),
            new Employee(4L, "Алексей Алексеев", "Менеджер", "Management", "БЦ2", 126L, "alex", Arrays.asList("lunch", "games"), true)
        );
    }
    
    @Test
    void testSimpleRandomMatching_Success() {
        // Тест успешного matching
        MatchingResult result = matchingService.simpleRandomMatching(testEmployees);
        
        assertNotNull(result);
        assertEquals("SIMPLE_RANDOM", result.getAlgorithm());
        assertEquals(2, result.getTotalPairs());
        assertEquals(0, result.getUnmatched().size());
        assertEquals(100.0, result.getSuccessRate());
        assertTrue(result.isSuccessful());
    }
    
    @Test
    void testSimpleRandomMatching_OddNumber() {
        // Тест с нечетным количеством сотрудников
        List<Employee> oddEmployees = testEmployees.subList(0, 3);
        MatchingResult result = matchingService.simpleRandomMatching(oddEmployees);
        
        assertNotNull(result);
        assertEquals(1, result.getTotalPairs());
        assertEquals(1, result.getUnmatched().size());
        assertEquals(66.7, result.getSuccessRate(), 0.1);
    }
    
    @Test
    void testSimpleRandomMatching_EmptyList() {
        // Тест с пустым списком
        MatchingResult result = matchingService.simpleRandomMatching(Collections.emptyList());
        
        assertNotNull(result);
        assertEquals(0, result.getTotalPairs());
        assertEquals(0, result.getUnmatched().size());
        assertEquals(0.0, result.getSuccessRate());
        assertFalse(result.isSuccessful());
    }
    
    @Test
    void testSimpleRandomMatching_SingleEmployee() {
        // Тест с одним сотрудником
        List<Employee> singleEmployee = Arrays.asList(testEmployees.get(0));
        MatchingResult result = matchingService.simpleRandomMatching(singleEmployee);
        
        assertNotNull(result);
        assertEquals(0, result.getTotalPairs());
        assertEquals(1, result.getUnmatched().size());
        assertEquals(0.0, result.getSuccessRate());
    }
    
    @Test
    void testInterestBasedMatching_Success() {
        // Тест matching по интересам
        MatchingResult result = matchingService.interestBasedMatching(testEmployees, "coffee");
        
        assertNotNull(result);
        assertEquals("SIMPLE_RANDOM", result.getAlgorithm()); // Использует простой алгоритм после фильтрации
        assertTrue(result.getTotalPairs() >= 1);
        assertEquals(3, result.getMatchedCount() + result.getUnmatched().size()); // 3 сотрудника с интересом "coffee"
    }
    
    @Test
    void testInterestBasedMatching_NoInterest() {
        // Тест с интересом, которого нет ни у кого
        MatchingResult result = matchingService.interestBasedMatching(testEmployees, "nonexistent");
        
        assertNotNull(result);
        assertEquals(0, result.getTotalPairs());
        assertEquals(4, result.getUnmatched().size());
    }
    
    @Test
    void testCrossDepartmentMatching_Success() {
        // Тест межотдельческого matching
        MatchingResult result = matchingService.crossDepartmentMatching(testEmployees);
        
        assertNotNull(result);
        assertEquals("CROSS_DEPARTMENT", result.getAlgorithm());
        assertTrue(result.getTotalPairs() >= 1);
        
        // Проверяем, что пары действительно из разных отделов
        result.getPairs().forEach(pair -> {
            String dept1 = pair.getEmployee1().getDepartment();
            String dept2 = pair.getEmployee2().getDepartment();
            assertNotEquals(dept1, dept2, "Сотрудники должны быть из разных отделов");
        });
    }
    
    @Test
    void testEmployeePairValidation() {
        Employee emp1 = testEmployees.get(0);
        Employee emp2 = testEmployees.get(1);
        
        // Валидная пара
        var validPair = new com.connectbot.matching.model.EmployeePair(emp1, emp2);
        assertTrue(validPair.isValid());
        
        // Невалидная пара (один и тот же сотрудник)
        var invalidPair = new com.connectbot.matching.model.EmployeePair(emp1, emp1);
        assertFalse(invalidPair.isValid());
    }
}