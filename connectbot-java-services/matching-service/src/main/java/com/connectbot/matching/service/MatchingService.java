package com.connectbot.matching.service;

import com.connectbot.matching.model.Employee;
import com.connectbot.matching.model.EmployeePair;
import com.connectbot.matching.model.MatchingResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Сервис алгоритмов matching для ConnectBot
 * 
 * @author ConnectBot Team
 * @version 1.0.0
 */
@Service
public class MatchingService {
    
    private static final Logger logger = LoggerFactory.getLogger(MatchingService.class);
    
    /**
     * Простой алгоритм случайного matching для кофе
     * 
     * @param employees список сотрудников
     * @return результат matching с парами
     */
    public MatchingResult simpleRandomMatching(List<Employee> employees) {
        logger.info("Запуск простого случайного matching для {} сотрудников", employees.size());
        
        // Валидация входных данных
        if (employees == null || employees.isEmpty()) {
            logger.warn("Пустой список сотрудников для matching");
            return new MatchingResult(Collections.emptyList(), Collections.emptyList(), "SIMPLE_RANDOM");
        }
        
        // Фильтруем только активных сотрудников
        List<Employee> activeEmployees = employees.stream()
            .filter(Employee::isActiveEmployee)
            .collect(Collectors.toList());
        
        logger.info("Активных сотрудников для matching: {}", activeEmployees.size());
        
        if (activeEmployees.size() < 2) {
            logger.warn("Недостаточно сотрудников для создания пар (нужно минимум 2)");
            return new MatchingResult(Collections.emptyList(), activeEmployees, "SIMPLE_RANDOM");
        }
        
        // Случайное перемешивание
        List<Employee> shuffledEmployees = new ArrayList<>(activeEmployees);
        Collections.shuffle(shuffledEmployees, new Random());
        
        // Создание пар
        List<EmployeePair> pairs = new ArrayList<>();
        List<Employee> unmatched = new ArrayList<>();
        
        for (int i = 0; i < shuffledEmployees.size(); i += 2) {
            if (i + 1 < shuffledEmployees.size()) {
                Employee emp1 = shuffledEmployees.get(i);
                Employee emp2 = shuffledEmployees.get(i + 1);
                
                EmployeePair pair = new EmployeePair(emp1, emp2);
                pairs.add(pair);
                
                logger.debug("Создана пара: {} & {}", emp1.getDisplayName(), emp2.getDisplayName());
            } else {
                // Нечетное количество - остается без пары
                unmatched.add(shuffledEmployees.get(i));
                logger.debug("Сотрудник {} остался без пары", shuffledEmployees.get(i).getDisplayName());
            }
        }
        
        MatchingResult result = new MatchingResult(pairs, unmatched, "SIMPLE_RANDOM");
        logger.info("Matching завершен: {} пар, {} без пары, успешность: {:.1f}%", 
            result.getTotalPairs(), unmatched.size(), result.getSuccessRate());
        
        return result;
    }
    
    /**
     * Алгоритм matching с учетом интересов
     * 
     * @param employees список сотрудников
     * @param interest конкретный интерес для фильтрации
     * @return результат matching
     */
    public MatchingResult interestBasedMatching(List<Employee> employees, String interest) {
        logger.info("Запуск interest-based matching для интереса '{}' и {} сотрудников", 
            interest, employees.size());
        
        if (employees == null || employees.isEmpty()) {
            return new MatchingResult(Collections.emptyList(), Collections.emptyList(), "INTEREST_BASED");
        }
        
        // Фильтруем сотрудников по интересу
        List<Employee> interestedEmployees = employees.stream()
            .filter(Employee::isActiveEmployee)
            .filter(emp -> emp.hasInterest(interest))
            .collect(Collectors.toList());
        
        logger.info("Сотрудников с интересом '{}': {}", interest, interestedEmployees.size());
        
        if (interestedEmployees.size() < 2) {
            List<Employee> unmatched = employees.stream()
                .filter(Employee::isActiveEmployee)
                .collect(Collectors.toList());
            return new MatchingResult(Collections.emptyList(), unmatched, "INTEREST_BASED");
        }
        
        // Применяем простой случайный алгоритм к отфильтрованным
        return simpleRandomMatching(interestedEmployees);
    }
    
    /**
     * Алгоритм matching с учетом отделов (избегаем коллег из одного отдела)
     * 
     * @param employees список сотрудников
     * @return результат matching
     */
    public MatchingResult crossDepartmentMatching(List<Employee> employees) {
        logger.info("Запуск cross-department matching для {} сотрудников", employees.size());
        
        if (employees == null || employees.isEmpty()) {
            return new MatchingResult(Collections.emptyList(), Collections.emptyList(), "CROSS_DEPARTMENT");
        }
        
        List<Employee> activeEmployees = employees.stream()
            .filter(Employee::isActiveEmployee)
            .collect(Collectors.toList());
        
        if (activeEmployees.size() < 2) {
            return new MatchingResult(Collections.emptyList(), activeEmployees, "CROSS_DEPARTMENT");
        }
        
        // Группируем по отделам
        Map<String, List<Employee>> departmentGroups = activeEmployees.stream()
            .collect(Collectors.groupingBy(emp -> 
                emp.getDepartment() != null ? emp.getDepartment() : "NO_DEPARTMENT"));
        
        List<EmployeePair> pairs = new ArrayList<>();
        List<Employee> unmatched = new ArrayList<>();
        Set<Employee> matched = new HashSet<>();
        
        // Пытаемся создать пары из разных отделов
        List<String> departments = new ArrayList<>(departmentGroups.keySet());
        
        for (int i = 0; i < departments.size(); i++) {
            for (int j = i + 1; j < departments.size(); j++) {
                List<Employee> dept1 = departmentGroups.get(departments.get(i));
                List<Employee> dept2 = departmentGroups.get(departments.get(j));
                
                // Создаем пары между отделами
                int pairsToCreate = Math.min(dept1.size(), dept2.size());
                for (int k = 0; k < pairsToCreate; k++) {
                    Employee emp1 = dept1.get(k);
                    Employee emp2 = dept2.get(k);
                    
                    if (!matched.contains(emp1) && !matched.contains(emp2)) {
                        pairs.add(new EmployeePair(emp1, emp2));
                        matched.add(emp1);
                        matched.add(emp2);
                    }
                }
            }
        }
        
        // Добавляем оставшихся в unmatched
        unmatched.addAll(activeEmployees.stream()
            .filter(emp -> !matched.contains(emp))
            .collect(Collectors.toList()));
        
        MatchingResult result = new MatchingResult(pairs, unmatched, "CROSS_DEPARTMENT");
        logger.info("Cross-department matching завершен: {} пар, {} без пары", 
            pairs.size(), unmatched.size());
        
        return result;
    }
}