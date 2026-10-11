package com.challengetotvs.api.domain.inicio;

import com.challengetotvs.api.security.ConsultorUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/inicio")
@RequiredArgsConstructor
public class InicioController {

    private final InicioService service;

    @GetMapping
    public ResponseEntity<InicioResponse> inicio(@AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.ok(service.montar(logado.getConsultor()));
    }
}