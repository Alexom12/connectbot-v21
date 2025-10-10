package com.connectbot.matching.controller;

import com.connectbot.matching.model.Employee;
import com.connectbot.matching.service.MatchingService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Arrays;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Тесты для SimpleMatchingController
 * 
 * @author ConnectBot Team
 * @version 1.0.0
 */
@WebMvcTest(SimpleMatchingController.class)
class SimpleMatchingControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private MatchingService matchingService;

    @Autowired
    private ObjectMapper objectMapper;

    private List<Employee> testEmployees;

    @BeforeEach
    void setUp() {
        testEmployees = Arrays.asList(
                new Employee(1L, "Test User 1", "Developer", "IT", "BC1", 123L, "user1", Arrays.asList("coffee"), true),
                new Employee(2L, "Test User 2", "Designer", "Design", "BC2", 124L, "user2", Arrays.asList("coffee"),
                        true));
    }

    @Test
    void testSimpleMatching_Success() throws Exception {
        // Мокаем сервис
        var mockResult = new com.connectbot.matching.model.MatchingResult();
        when(matchingService.simpleRandomMatching(any())).thenReturn(mockResult);

        // Выполняем запрос
        mockMvc.perform(post("/api/matching/coffee/simple")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(testEmployees)))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON));
    }

    @Test
    void testGetAlgorithms_Success() throws Exception {
        mockMvc.perform(get("/api/matching/algorithms"))
                .andExpected(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpected(jsonPath("$.algorithms").exists())
                .andExpect(jsonPath("$.total").value(3));
    }

    @Test
    void testInterestBasedMatching_Success() throws Exception {
        var mockResult = new com.connectbot.matching.model.MatchingResult();
        when(matchingService.interestBasedMatching(any(), any())).thenReturn(mockResult);

        mockMvc.perform(post("/api/matching/coffee/interest")
                .param("interest", "coffee")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(testEmployees)))
                .andExpect(status().isOk());
    }
}