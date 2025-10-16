package com.connectbot.matching.controller;

import com.connectbot.matching.service.MatchingService;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import static org.junit.jupiter.api.Assertions.*;

import java.util.Map;

public class MatchingControllerV1Test {

    @Test
    public void testHealthDegradedWhenServiceUnhealthy() {
        MatchingService svc = Mockito.mock(MatchingService.class);
        Mockito.when(svc.isHealthy()).thenReturn(false);
        MatchingControllerV1 ctrl = new MatchingControllerV1();
        // inject mocked service via reflection
        try {
            java.lang.reflect.Field f = MatchingControllerV1.class.getDeclaredField("matchingService");
            f.setAccessible(true);
            f.set(ctrl, svc);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        ResponseEntity<?> r = ctrl.healthCheck();
        assertEquals(HttpStatus.SERVICE_UNAVAILABLE, r.getStatusCode());
    }

    @Test
    public void testMatchFromApiHandlesErrors() {
        MatchingService svc = Mockito.mock(MatchingService.class);
        try {
            java.lang.reflect.Field f = MatchingControllerV1.class.getDeclaredField("matchingService");
            f.setAccessible(true);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        MatchingControllerV1 ctrl = new MatchingControllerV1();
        try {
            java.lang.reflect.Field f = MatchingControllerV1.class.getDeclaredField("matchingService");
            f.setAccessible(true);
            f.set(ctrl, svc);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        Mockito.when(svc.runSecretCoffeeFromApi(Mockito.anyMap())).thenThrow(new RuntimeException("boom"));
        ResponseEntity<?> r = ctrl.runSecretCoffeeFromApi(Map.of());
        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, r.getStatusCode());
    }
}
