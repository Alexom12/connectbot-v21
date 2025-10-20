package com.connectbot.matching.service;

import com.connectbot.matching.model.Employee;
import com.connectbot.matching.model.EmployeePair;
import com.connectbot.matching.model.MatchingResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.*;
import java.util.stream.Collectors;
import com.connectbot.matching.dto.EmployeeDTO;
import com.connectbot.matching.client.DataApiClient;
import com.connectbot.matching.dto.dataapi.DataApiEmployeesResponseDTO;
import org.springframework.web.client.RestClientException;
import com.connectbot.matching.dto.MatchingRequestDTO;
import com.connectbot.matching.dto.EmployeePairDTO;
import com.connectbot.matching.dto.MatchingResponseDTO;

/**
 * Сервис алгоритмов matching для ConnectBot
 * 
 * @author ConnectBot Team
 * @version 1.0.0
 */
@Service
public class MatchingService {

    private static final Logger logger = LoggerFactory.getLogger(MatchingService.class);
    private final DataApiClient dataApiClient;

    @Autowired
    public MatchingService(DataApiClient dataApiClient) {
        this.dataApiClient = dataApiClient;
    }

    /**
     * Простой алгоритм случайного matching для кофе
     * 
     * @param employees список сотрудников
     * @return результат matching с парами
     */
    public MatchingResult simpleRandomMatching(List<Employee> employees) {
        logger.info("🔥 HOT-RELOAD TEST: v2 🔥 Запуск простого случайного matching для {} сотрудников",
                employees.size());

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
     * Adapter: принимает DTO-запрос и возвращает DTO-результат для совместимости с
     * V1 API
     */
    public MatchingResponseDTO runSecretCoffee(MatchingRequestDTO request) {
        logger.info("Starting secret coffee matching, request_id={}", request.getRequestId());

        // 1. Получить данные о сотрудниках из Data API
        DataApiEmployeesResponseDTO employeesResponse;
        try {
            employeesResponse = dataApiClient.getEmployeesForMatching(request.getAlgorithmParams());
        } catch (RestClientException e) {
            logger.error("Failed to get employees from Data API: {}", e.getMessage());
            // Consider a more specific error DTO
            return new MatchingResponseDTO(request.getRequestId(), "error", "data_api_failed", null, null);
        }

        if (employeesResponse == null || employeesResponse.getEmployees() == null) {
            logger.warn("Data API returned null or empty employee list");
            return new MatchingResponseDTO(request.getRequestId(), "error", "no_employees_from_api", null, null);
        }

        List<Employee> employees = employeesResponse.getEmployees().stream()
                .map(Employee::fromDTO)
                .collect(Collectors.toList());

        logger.info("Received {} employees from Data API", employees.size());

        // 2. Выполнить matching
        MatchingResult result = simpleRandomMatching(employees);
        logger.info("Matching complete, created {} pairs", result.getPairs().size());

        // 3. Преобразовать результат в DTO
        List<EmployeePairDTO> pairDTOs = result.getPairs().stream()
                .map(EmployeePair::toDTO)
                .collect(Collectors.toList());

        MatchingResponseDTO randomResult = new MatchingResponseDTO(
                request.getRequestId(),
                "ok",
                null,
                pairDTOs,
                result.getMeta());
        randomResult.setAlgorithm("simple_random");
        return randomResult;
    }

    /**
     * Run secret coffee matching by fetching employees from Data API using provided
     * body parameters.
     */
    public MatchingResponseDTO runSecretCoffeeFromApi(java.util.Map<String, Object> body) {
        try {
            DataApiEmployeesResponseDTO resp = dataApiClient.getEmployeesForMatching(body);
            MatchingRequestDTO request = new MatchingRequestDTO();
            request.setEmployees(resp.getEmployees());
            return runSecretCoffee(request);
        } catch (RestClientException ex) {
            logger.error("Failed to fetch employees from Data API: {}", ex.getMessage());
            throw ex;
        }
    }

    public boolean isHealthy() {
        try {
            return dataApiClient == null || dataApiClient.healthCheck();
        } catch (Exception ex) {
            logger.warn("MatchingService health check failed: {}", ex.getMessage());
            return false;
        }
    }

    /**
     * Алгоритм matching с учетом интересов
     * 
     * @param employees список сотрудников
     * @param interest  конкретный интерес для фильтрации
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
                .collect(Collectors
                        .groupingBy(emp -> emp.getDepartment() != null ? emp.getDepartment() : "NO_DEPARTMENT"));

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

    /**
     * Пример сложного алгоритма matching (пока просто вызывает случайный)
     * 
     * @param request параметры запроса
     * @return результат matching
     */
    public MatchingResponseDTO runAdvancedMatching(MatchingRequestDTO request) {
        logger.info("Запуск продвинутого matching для запроса {}", request.getRequestId());

        // Здесь может быть сложная логика, пока просто случайный
        MatchingResponseDTO randomResult = runSecretCoffee(request);

        // Пример модификации результата
        randomResult.setRequestId(request.getRequestId());
        randomResult.setAlgorithm("ADVANCED_RANDOM");

        logger.info("Продвинутый matching завершен для запроса {}", request.getRequestId());
        return randomResult;
    }
}