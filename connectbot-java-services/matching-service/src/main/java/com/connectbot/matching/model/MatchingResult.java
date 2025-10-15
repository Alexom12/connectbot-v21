package com.connectbot.matching.model;

import java.util.List;

/**
 * Минимальная модель результата matching.
 */
public class MatchingResult {
    private List<EmployeePair> pairs;
    private List<Employee> unmatched;
    private String algorithm;

    public MatchingResult() {
    }

    public MatchingResult(List<EmployeePair> pairs, List<Employee> unmatched, String algorithm) {
        this.pairs = pairs;
        this.unmatched = unmatched;
        this.algorithm = algorithm;
    }

    public List<EmployeePair> getPairs() {
        return pairs;
    }

    public void setPairs(List<EmployeePair> pairs) {
        this.pairs = pairs;
    }

    public List<Employee> getUnmatched() {
        return unmatched;
    }

    public void setUnmatched(List<Employee> unmatched) {
        this.unmatched = unmatched;
    }

    public String getAlgorithm() {
        return algorithm;
    }

    public void setAlgorithm(String algorithm) {
        this.algorithm = algorithm;
    }

    public int getTotalPairs() {
        return pairs != null ? pairs.size() : 0;
    }

    public double getSuccessRate() {
        int total = (pairs != null ? pairs.size() * 2 : 0) + (unmatched != null ? unmatched.size() : 0);
        if (total == 0)
            return 0.0;
        return (double) (pairs != null ? pairs.size() * 2 : 0) / total * 100.0;
    }

    // Количество сопоставленных сотрудников (в парах)
    public int getMatchedCount() {
        return pairs != null ? pairs.size() * 2 : 0;
    }

    // Успешность — признак того, что хотя бы одна пара создана
    public boolean isSuccessful() {
        return getMatchedCount() > 0;
    }
}
