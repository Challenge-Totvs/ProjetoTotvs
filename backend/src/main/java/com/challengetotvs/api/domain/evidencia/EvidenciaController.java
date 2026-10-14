package com.challengetotvs.api.domain.evidencia;

import com.challengetotvs.api.security.ConsultorUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/clientes")
@RequiredArgsConstructor
public class EvidenciaController {

    private final EvidenciaService service;

    @GetMapping("/{id}/evidencias")
    public ResponseEntity<EvidenciaResponse> buscar(@PathVariable Long id,
                                                    @RequestParam(required = false) String q,
                                                    @AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.ok(service.buscar(id, q, logado.getConsultor()));
    }
}
