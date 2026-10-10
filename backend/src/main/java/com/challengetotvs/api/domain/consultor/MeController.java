package com.challengetotvs.api.domain.consultor;

import com.challengetotvs.api.security.ConsultorUserDetails;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/me")
public class MeController {

    /** Quem está logado. O frontend chama ao abrir a aplicação com um token salvo. */
    @GetMapping
    public ResponseEntity<UsuarioResponse> me(@AuthenticationPrincipal ConsultorUserDetails usuarioLogado) {
        return ResponseEntity.ok(UsuarioResponse.de(usuarioLogado.getConsultor()));
    }
}
