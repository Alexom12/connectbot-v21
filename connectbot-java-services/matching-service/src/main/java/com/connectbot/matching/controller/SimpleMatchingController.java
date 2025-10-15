package com.connectbot.matching.controller;

import com.connectbot.matching.model.Employee;
import com.connectbot.matching.model.MatchingResult;
import com.connectbot.matching.service.MatchingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/matching")
public class SimpleMatchingController {

    @Autowired
    private MatchingService matchingService;

    @GetMapping("/algorithms")
    public ResponseEntity<Map<String, Object>> getAlgorithms() {
        Map<String, Object> resp = new HashMap<>();
        resp.put("algorithms", List.of("SIMPLE_RANDOM", "INTEREST_BASED", "CROSS_DEPARTMENT"));
        resp.put("total", 3);
        return ResponseEntity.ok(resp);
    }

    @PostMapping("/coffee/simple")
    public ResponseEntity<MatchingResult> simpleCoffee(@RequestBody List<Employee> employees) {
        MatchingResult res = matchingService.simpleRandomMatching(employees);
        return ResponseEntity.ok(res);
    }

    @PostMapping("/coffee/interest")
    public ResponseEntity<MatchingResult> interestCoffee(@RequestBody List<Employee> employees,
            @RequestParam String interest) {
        MatchingResult res = matchingService.interestBasedMatching(employees, interest);
        return ResponseEntity.ok(res);
    }
}
