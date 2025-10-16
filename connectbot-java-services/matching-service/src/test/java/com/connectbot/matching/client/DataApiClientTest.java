package com.connectbot.matching.client;

import com.connectbot.matching.dto.dataapi.DataApiEmployeesResponseDTO;
import com.connectbot.matching.dto.EmployeeDTO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentMatchers;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
public class DataApiClientTest {

    @Mock
    private RestTemplate restTemplate;

    private DataApiClient client;

    @BeforeEach
    public void setup() {
        client = new DataApiClient(restTemplate, "http://localhost:8000", "token-x", 3, 10);
    }

    @Test
    public void testRetriesThenSuccess() {
        DataApiEmployeesResponseDTO dto = new DataApiEmployeesResponseDTO();
        dto.setEmployees(Collections.singletonList(new EmployeeDTO()));

        when(restTemplate.exchange(ArgumentMatchers.anyString(), ArgumentMatchers.eq(HttpMethod.POST), ArgumentMatchers.any(), ArgumentMatchers.eq(DataApiEmployeesResponseDTO.class)))
                .thenThrow(new RestClientException("temporary"))
                .thenReturn(ResponseEntity.ok(dto));

        Map<String,Object> body = new HashMap<>();
        DataApiEmployeesResponseDTO res = client.getEmployeesForMatching(body);
        assertNotNull(res);
        assertNotNull(res.getEmployees());
        verify(restTemplate, atLeast(2)).exchange(ArgumentMatchers.anyString(), ArgumentMatchers.eq(HttpMethod.POST), ArgumentMatchers.any(), ArgumentMatchers.eq(DataApiEmployeesResponseDTO.class));
    }

    @Test
    public void testExhaustRetries() {
        when(restTemplate.exchange(ArgumentMatchers.anyString(), ArgumentMatchers.eq(HttpMethod.POST), ArgumentMatchers.any(), ArgumentMatchers.eq(DataApiEmployeesResponseDTO.class)))
                .thenThrow(new RestClientException("fail1"));

        Map<String,Object> body = new HashMap<>();
        assertThrows(RestClientException.class, () -> client.getEmployeesForMatching(body));
        verify(restTemplate, times(3)).exchange(ArgumentMatchers.anyString(), ArgumentMatchers.eq(HttpMethod.POST), ArgumentMatchers.any(), ArgumentMatchers.eq(DataApiEmployeesResponseDTO.class));
    }
}
