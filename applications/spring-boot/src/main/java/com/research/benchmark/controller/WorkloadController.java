package com.research.benchmark.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class WorkloadController {

    /**
     * CPU-bound workload: compute primes up to a limit to consume CPU for approximately durationMs.
     * Default 200ms matches experiment config.
     */
    @GetMapping("/cpu/work")
    public ResponseEntity<Map<String, Object>> cpuWork(
            @RequestParam(defaultValue = "200") int durationMs
    ) {
        long start = System.currentTimeMillis();
        int count = 0;
        int n = 2;

        while (System.currentTimeMillis() - start < durationMs) {
            if (isPrime(n)) {
                count++;
            }
            n++;
        }

        Map<String, Object> result = new HashMap<>();
        result.put("primesFound", count);
        result.put("durationMs", System.currentTimeMillis() - start);
        result.put("framework", "spring-boot");
        return ResponseEntity.ok(result);
    }

    /**
     * I/O-bound workload: simulates database delay using Thread.sleep.
     * Matches FastAPI's asyncio.sleep for fair comparison.
     */
    @GetMapping("/io/delay")
    public ResponseEntity<Map<String, Object>> ioDelay(
            @RequestParam(defaultValue = "200") int delayMs
    ) {
        long start = System.currentTimeMillis();
        try {
            Thread.sleep(Math.min(delayMs, 5000)); // Cap at 5s for safety
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return ResponseEntity.status(503).build();
        }

        Map<String, Object> result = new HashMap<>();
        result.put("delayMs", delayMs);
        result.put("actualMs", System.currentTimeMillis() - start);
        result.put("framework", "spring-boot");
        return ResponseEntity.ok(result);
    }

    private boolean isPrime(int n) {
        if (n <= 1) return false;
        if (n <= 3) return true;
        if (n % 2 == 0 || n % 3 == 0) return false;
        for (int i = 5; i * i <= n; i = i + 6) {
            if (n % i == 0 || n % (i + 2) == 0) return false;
        }
        return true;
    }
}