package com.challengetotvs.api.domain.padrao;

import com.challengetotvs.api.domain.tema.PadraoRepository;
import com.challengetotvs.api.security.ConsultorUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/padroes")
@RequiredArgsConstructor
public class PadraoController {

    private final PadraoRepository padraoRepository;
    private final PadraoAgregadoService agregadoService;

    public record PadraoItem(String chave, String nome, String tipo) {
    }

    @GetMapping
    public ResponseEntity<List<PadraoItem>> listar() {
        var itens = padraoRepository.findByAtivoTrueOrderByNomeAsc().stream()
                .map(p -> new PadraoItem(p.getChave(), p.getNome(), p.getTipo().valor()))
                .toList();
        return ResponseEntity.ok(itens);
    }

    @GetMapping("/agregado")
    public ResponseEntity<List<PadraoAgregadoResponse>> agregado(
            @RequestParam(defaultValue = "todos") String tipoCliente,
            @RequestParam(defaultValue = "todos") String tipo,
            @AuthenticationPrincipal ConsultorUserDetails logado) {
        return ResponseEntity.ok(agregadoService.agregar(tipoCliente, tipo, logado.getConsultor()));
    }
}