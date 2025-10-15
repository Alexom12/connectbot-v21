package com.connectbot.matching.controller;

import com.connectbot.matching.dto.HealthStatusDTO;
import com.connectbot.matching.dto.MatchingRequestDTO;
import com.connectbot.matching.dto.MatchingResponseDTO;
import com.connectbot.matching.service.MatchingService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * REST контроллер для V1 API сервиса подбора пар.
 * Реализует эндпоинты, определенные в OpenAPI спецификации.
 */
@RestController
@RequestMapping("/api/v1/matching")
@CrossOrigin(origins = "*")
public class MatchingControllerV1 {

    private static final Logger logger = LoggerFactory.getLogger(MatchingControllerV1.class);

    @Autowired
    private MatchingService matchingService;

    /**
     * Эндпоинт для проверки состояния здоровья сервиса.
     *
     * @return Статус "OK", если сервис работает.
     */
    @GetMapping("/health")
    public ResponseEntity<HealthStatusDTO> healthCheck() {
        logger.info("V1 health check-запрос получен");
        return ResponseEntity.ok(new HealthStatusDTO("OK"));
    }

    /**
     * Основной эндпоинт для запуска алгоритма подбора пар "Секретный кофе".
     *
     * @param request DTO с данными сотрудников для подбора.
     * @return DTO с результатом подбора - списком пар.
     */
    @PostMapping("/match/secret-coffee")
    public ResponseEntity<MatchingResponseDTO> runSecretCoffeeMatching(@RequestBody MatchingRequestDTO request) {
        if (request == null || request.getEmployees() == null || request.getEmployees().isEmpty()) {
            logger.warn("Запрос на подбор пришел с пустым списком сотрудников.");
            return ResponseEntity.badRequest().build();
        }

        logger.info("V1 secret-coffee-запрос получен для {} сотрудников", request.getEmployees().size());

        try {
            // Здесь будет вызов обновленного сервисного метода
            // Пока что возвращаем заглушку
            MatchingResponseDTO response = matchingService.runSecretCoffee(request);
            logger.info("V1 secret-coffee-подбор выполнен, найдено {} пар.", response.getPairs().size());
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Ошибка в процессе V1 secret-coffee-подбора: {}", e.getMessage(), e);
            // В будущем здесь будет более детальная обработка ошибок
            return ResponseEntity.internalServerError().build();
        }
    }
}
