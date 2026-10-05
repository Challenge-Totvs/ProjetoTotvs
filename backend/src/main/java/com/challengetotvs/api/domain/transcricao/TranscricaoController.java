package com.challengetotvs.api.domain.transcricao;

import com.challengetotvs.api.domain.analise.AnaliseService;
import com.challengetotvs.api.domain.analise.ResultadoAnalise;
import com.challengetotvs.api.domain.consultor.Consultor;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class TranscricaoController {

    private final TranscricaoService transcricaoService;
    private final AnaliseService analiseService;

    @PostMapping("/transcricoes/{id}/analisar")
    public ResponseEntity<ResultadoAnalise> analisar(@PathVariable Long id, @AuthenticationPrincipal Consultor consultor) {
        return ResponseEntity.ok(analiseService.analisar(id, consultor));
    }

    @GetMapping("/transcricoes/{id}/analise")
    public ResponseEntity<ResultadoAnalise> buscar(@PathVariable Long id, @AuthenticationPrincipal Consultor consultor) {
        return ResponseEntity.ok(analiseService.buscar(id, consultor));
    }
}
