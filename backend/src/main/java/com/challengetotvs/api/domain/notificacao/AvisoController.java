package com.challengetotvs.api.domain.notificacao;

import com.challengetotvs.api.security.ConsultorUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class AvisoController {

    private final AvisoService service;

    @PostMapping("/temas/{id}/avisos")
    public ResponseEntity<NotificacaoResponse.Item> avisar(
            @PathVariable Long id,
            @RequestBody(required = false) Map<String, String> corpo,
            @AuthenticationPrincipal ConsultorUserDetails logado) {
        var mensagem = corpo == null ? null : corpo.get("mensagem");
        var criado = service.avisar(id, mensagem, logado.getConsultor());
        return ResponseEntity.status(HttpStatus.CREATED).body(criado);
    }

    @DeleteMapping("/avisos/{id}")
    public ResponseEntity<Void> desfazer(@PathVariable Long id, @AuthenticationPrincipal ConsultorUserDetails logado) {
        service.desfazer(id, logado.getConsultor());
        return ResponseEntity.noContent().build(); // 204
    }

    @GetMapping("/notificacoes")
    public ResponseEntity<NotificacaoResponse> listar(@AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.ok(service.listar(logado.getConsultor()));
    }

    @PatchMapping("/notificacoes/{id}")
    public ResponseEntity<Void> marcarLida(@PathVariable Long id, @RequestBody PatchNotificacaoRequest corpo, @AuthenticationPrincipal ConsultorUserDetails logado) {
        service.marcarLida(id, corpo.lida(), logado.getConsultor());
        return ResponseEntity.ok().build();
    }
}