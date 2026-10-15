package com.challengetotvs.api.domain.vendedor;

import com.challengetotvs.api.domain.inicio.InicioResponse;
import com.challengetotvs.api.security.ConsultorUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/vendedores")
@RequiredArgsConstructor
public class VendedorController {

    private final VendedorService service;

    @GetMapping
    public ResponseEntity<List<VendedorResumo>> listar(@AuthenticationPrincipal ConsultorUserDetails logado,
                                                        @RequestParam(required = false) Integer janelaDias) {
        return ResponseEntity.ok(service.listar(logado.getConsultor(), janelaDias));
    }

    @GetMapping("/{id}/inicio")
    public ResponseEntity<InicioResponse> inicio(@PathVariable Long id,
                                                 @AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.ok(service.inicioDe(id, logado.getConsultor()));
    }
}