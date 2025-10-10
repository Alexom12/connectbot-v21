package com.connectbot.matching.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * Health Check контроллер для мониторинга состояния сервиса
 * 
 * @author ConnectBot Team
 * @version 1.0.0
 */
@RestController
@RequestMapping("/api/matching")
@CrossOrigin(origins = "*")
public class HealthController {
    
    private static final Logger logger = LoggerFactory.getLogger(HealthController.class);
    
    @Autowired(required = false)
    private RedisConnectionFactory redisConnectionFactory;
    
    /**
     * Базовая проверка здоровья сервиса
     * 
     * @return статус сервиса
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        logger.debug("Health check запрос получен");
        
        Map<String, Object> healthStatus = new HashMap<>();
        
        // Основной статус
        healthStatus.put("status", "UP");
        healthStatus.put("service", "ConnectBot Matching Service");
        healthStatus.put("version", "1.0.0");
        healthStatus.put("timestamp", LocalDateTime.now());
        
        // Проверка Redis подключения
        Map<String, Object> redisStatus = checkRedisConnection();
        healthStatus.put("redis", redisStatus);
        
        // Проверка памяти
        Runtime runtime = Runtime.getRuntime();
        long totalMemory = runtime.totalMemory();
        long freeMemory = runtime.freeMemory();
        long usedMemory = totalMemory - freeMemory;
        
        Map<String, Object> memoryStatus = new HashMap<>();
        memoryStatus.put("total", totalMemory);
        memoryStatus.put("used", usedMemory);
        memoryStatus.put("free", freeMemory);
        memoryStatus.put("usage_percent", Math.round((double) usedMemory / totalMemory * 100));
        
        healthStatus.put("memory", memoryStatus);
        
        // Общий статус
        boolean isHealthy = "UP".equals(redisStatus.get("status"));
        healthStatus.put("overall_status", isHealthy ? "HEALTHY" : "DEGRADED");
        
        HttpStatus httpStatus = isHealthy ? HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;
        
        logger.info("Health check выполнен: статус = {}, Redis = {}", 
            healthStatus.get("overall_status"), redisStatus.get("status"));
        
        return ResponseEntity.status(httpStatus).body(healthStatus);
    }
    
    /**
     * Детальная проверка здоровья сервиса
     * 
     * @return расширенная информация о состоянии
     */
    @GetMapping("/health/detailed")
    public ResponseEntity<Map<String, Object>> detailedHealth() {
        logger.debug("Detailed health check запрос получен");
        
        Map<String, Object> detailedStatus = new HashMap<>();
        
        // Базовая информация
        detailedStatus.put("service_name", "ConnectBot Matching Service");
        detailedStatus.put("version", "1.0.0");
        detailedStatus.put("timestamp", LocalDateTime.now());
        detailedStatus.put("uptime_ms", System.currentTimeMillis());
        
        // Системная информация
        Map<String, Object> systemInfo = new HashMap<>();
        systemInfo.put("java_version", System.getProperty("java.version"));
        systemInfo.put("os_name", System.getProperty("os.name"));
        systemInfo.put("os_version", System.getProperty("os.version"));
        systemInfo.put("processors", Runtime.getRuntime().availableProcessors());
        
        detailedStatus.put("system", systemInfo);
        
        // Проверка компонентов
        Map<String, Object> components = new HashMap<>();
        components.put("redis", checkRedisConnection());
        components.put("matching_service", Map.of("status", "UP", "algorithms", 3));
        
        detailedStatus.put("components", components);
        
        // Метрики
        Runtime runtime = Runtime.getRuntime();
        Map<String, Object> metrics = new HashMap<>();
        metrics.put("memory_total_mb", runtime.totalMemory() / 1024 / 1024);
        metrics.put("memory_free_mb", runtime.freeMemory() / 1024 / 1024);
        metrics.put("memory_used_mb", (runtime.totalMemory() - runtime.freeMemory()) / 1024 / 1024);
        metrics.put("memory_max_mb", runtime.maxMemory() / 1024 / 1024);
        
        detailedStatus.put("metrics", metrics);
        
        return ResponseEntity.ok(detailedStatus);
    }
    
    /**
     * Проверка статуса Redis подключения
     * 
     * @return статус Redis
     */
    private Map<String, Object> checkRedisConnection() {
        Map<String, Object> redisStatus = new HashMap<>();
        
        if (redisConnectionFactory == null) {
            redisStatus.put("status", "NOT_CONFIGURED");
            redisStatus.put("message", "Redis не сконфигурирован");
            return redisStatus;
        }
        
        try {
            // Попытка получить соединение
            redisConnectionFactory.getConnection().ping();
            redisStatus.put("status", "UP");
            redisStatus.put("message", "Redis доступен");
            
        } catch (Exception e) {
            logger.warn("Redis недоступен: {}", e.getMessage());
            redisStatus.put("status", "DOWN");
            redisStatus.put("message", "Redis недоступен: " + e.getMessage());
        }
        
        return redisStatus;
    }
}