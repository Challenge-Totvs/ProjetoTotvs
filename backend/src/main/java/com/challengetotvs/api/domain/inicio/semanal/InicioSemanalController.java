package com.challengetotvs.api.domain.inicio.semanal;

import com.challengetotvs.api.security.ConsultorUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/inicio/semanal")
@RequiredArgsConstructor
public class InicioSemanalController {

    private final InicioSemanalService service;

    @GetMapping
    public ResponseEntity<InicioSemanalResponse> semanal(
            @AuthenticationPrincipal ConsultorUserDetails logado,
            @RequestParam(required = false) Integer janelaDias) {
        return ResponseEntity.ok(service.montar(logado.getConsultor(), janelaDias));
    }
}
