package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.security.ConsultorUserDetails;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/temas")
@RequiredArgsConstructor
public class TemaController {

    private final TemaAcaoService service;

    @PostMapping("/{id}/tratado-fora")
    public ResponseEntity<TemaResponse> registrarFora(@PathVariable Long id, @RequestBody @Valid TratadoForaRequest request, @AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(service.registrarForaDaReuniao(id, request, logado.getConsultor()));
    }

    @DeleteMapping("/{id}/tratado-fora")
    public ResponseEntity<TemaResponse> removerFora(@PathVariable Long id, @AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.ok(service.removerForaDaReuniao(id, logado.getConsultor()));
    }

    @PostMapping("/{id}/nao-procede")
    public ResponseEntity<TemaResponse> marcarNaoProcede(@PathVariable Long id, @RequestBody(required = false) NaoProcedeRequest request, @AuthenticationPrincipal ConsultorUserDetails logado) {
        String motivo = request == null ? null : request.motivo();
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(service.marcarNaoProcede(id, motivo, logado.getConsultor()));
    }

    @DeleteMapping("/{id}/nao-procede")
    public ResponseEntity<TemaResponse> desfazerNaoProcede(@PathVariable Long id, @AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.ok(service.desfazerNaoProcede(id, logado.getConsultor()));
    }
}