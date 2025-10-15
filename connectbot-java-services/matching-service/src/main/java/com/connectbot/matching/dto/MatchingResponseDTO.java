package com.connectbot.matching.dto;

import java.util.List;

/**
 * DTO для ответа с результатами подбора.
 */
public class MatchingResponseDTO {

    private List<EmployeePairDTO> pairs;

    // Getters and Setters

    public List<EmployeePairDTO> getPairs() {
        return pairs;
    }

    public void setPairs(List<EmployeePairDTO> pairs) {
        this.pairs = pairs;
    }
}
