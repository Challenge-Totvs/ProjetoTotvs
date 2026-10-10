package com.challengetotvs.api.domain.cliente;

import com.challengetotvs.api.security.ConsultorUserDetails;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/clientes")
@RequiredArgsConstructor
public class ClienteController {

    private final ClienteService service;

    @PostMapping
    public ResponseEntity<ClienteResponse> criar(@RequestBody @Valid ClienteRequest request,
                                                 @AuthenticationPrincipal ConsultorUserDetails logado) {
        var criado = service.criar(request, logado.getConsultor());
        return ResponseEntity.status(HttpStatus.CREATED).body(criado);
    }

    @GetMapping
    public ResponseEntity<List<ClienteResponse>> listar(@AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.ok(service.listar(logado.getConsultor()));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ClienteResponse> buscar(@PathVariable Long id,
                                                  @AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.ok(service.buscar(id, logado.getConsultor()));
    }
}