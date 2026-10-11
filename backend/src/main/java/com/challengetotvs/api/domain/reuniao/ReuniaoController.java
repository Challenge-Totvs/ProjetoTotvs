package com.challengetotvs.api.domain.reuniao;

import com.challengetotvs.api.domain.transcricao.EnviarTranscricaoResponse;
import com.challengetotvs.api.domain.transcricao.TranscricaoRequest;
import com.challengetotvs.api.domain.transcricao.TranscricaoResponse;
import com.challengetotvs.api.domain.transcricao.TranscricaoService;
import com.challengetotvs.api.security.ConsultorUserDetails;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import com.challengetotvs.api.domain.reuniao.ReuniaoDetalheResponse.TurnoResponse;   // mesmo pacote do controller: só a linha de TurnoResponse é necessária
import java.util.List;

@RestController
@RequestMapping("/api/reunioes")
@RequiredArgsConstructor
public class ReuniaoController {

    private final ReuniaoService service;
    private final TranscricaoService transcricaoService;
    private final ReuniaoDetalhador detalhador;

    @PostMapping
    public ResponseEntity<ReuniaoResponse> criar(@RequestBody @Valid ReuniaoRequest request, @AuthenticationPrincipal ConsultorUserDetails userDetails){
        var criada = service.criar(request, userDetails.getConsultor());
        return ResponseEntity.status(HttpStatus.CREATED).body(criada);
    }

    @GetMapping
    public ResponseEntity<Page<ReuniaoResponse>> listarTodos(@PageableDefault(size = 10, sort = {"dataHora"})Pageable pagination, @AuthenticationPrincipal ConsultorUserDetails userDetails){
        var consultor = userDetails.getConsultor();
        var reuniao = service.listar(pagination, consultor);
        return ResponseEntity.ok(reuniao);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ReuniaoDetalheResponse> detalhar(@PathVariable Long id, @AuthenticationPrincipal ConsultorUserDetails userDetails) {
        return ResponseEntity.ok(detalhador.montar(id, userDetails.getConsultor()));
    }

    @PatchMapping("/{id}/status")
    public ResponseEntity<ReuniaoResponse> atualizarStatus(@PathVariable Long id, @RequestParam StatusReuniao status, @AuthenticationPrincipal ConsultorUserDetails userDetails){
        var consultor = userDetails.getConsultor();
        var reuniao = service.atualizarStatus(id, status, consultor);
        return ResponseEntity.ok(reuniao);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deletar(@PathVariable Long id, @AuthenticationPrincipal ConsultorUserDetails userDetails){
        var consultor = userDetails.getConsultor();
        service.excluir(id, consultor);
        return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
    }

    @PostMapping("/{id}/transcricao")
    public ResponseEntity<EnviarTranscricaoResponse> enviarTranscricao(@PathVariable Long id, @RequestBody @Valid TranscricaoRequest request, @AuthenticationPrincipal ConsultorUserDetails userDetails){
        var resposta = transcricaoService.enviar(id, request, userDetails.getConsultor());
        return ResponseEntity.status(HttpStatus.CREATED).body(resposta);
    }

    @GetMapping("/{id}/transcricao")
    public ResponseEntity<List<TurnoResponse>> transcricao(@PathVariable Long id, @RequestParam(required = false) String versao, @AuthenticationPrincipal ConsultorUserDetails userDetails) {
        return ResponseEntity.ok(detalhador.transcricao(id, versao, userDetails.getConsultor()));
    }
}
