package com.challengetotvs.api.domain.transcricao;

import com.challengetotvs.api.domain.analise.AnalisarResponse;
import com.challengetotvs.api.domain.analise.AnaliseService;
import com.challengetotvs.api.security.ConsultorUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class TranscricaoController {

    private final AnaliseService analiseService;

    @PostMapping("/transcricoes/{id}/analisar")
    public ResponseEntity<AnalisarResponse> analisar(@PathVariable Long id,
                                                     @AuthenticationPrincipal ConsultorUserDetails userDetails) {
        return ResponseEntity.ok(analiseService.analisar(id, userDetails.getConsultor()));
    }
}