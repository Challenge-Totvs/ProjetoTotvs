package com.challengetotvs.api.domain.compromisso;

import com.challengetotvs.api.security.ConsultorUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/compromissos")
@RequiredArgsConstructor
public class CompromissoController {

    private final CompromissoService service;

    public record PatchRequest(boolean cumprido) {
    }

    @GetMapping
    public ResponseEntity<List<CompromissoResponse>> listar(
            @RequestParam(required = false) Long vendedorId,
            @RequestParam(required = false) Long clienteId,
            @RequestParam(required = false) Long reuniaoId,
            @AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.ok(service.listar(vendedorId, clienteId, reuniaoId, logado.getConsultor()));
    }

    @PatchMapping("/{id}")
    public ResponseEntity<CompromissoResponse> marcar(@PathVariable Long id, @RequestBody PatchRequest corpo, @AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.ok(service.marcar(id, corpo.cumprido(), logado.getConsultor()));
    }
}