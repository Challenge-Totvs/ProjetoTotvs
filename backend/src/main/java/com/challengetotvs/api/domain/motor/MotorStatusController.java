package com.challengetotvs.api.domain.motor;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/motores")
@RequiredArgsConstructor
public class MotorStatusController {

    private final MotorStatusService service;

    @GetMapping("/status")
    public ResponseEntity<List<MotorStatus>> status() {
        return ResponseEntity.ok(service.status());
    }
}