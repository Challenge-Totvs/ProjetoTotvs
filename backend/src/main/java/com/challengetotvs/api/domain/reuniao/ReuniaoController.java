package com.challengetotvs.api.domain.reuniao;

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

@RestController
@RequestMapping("/api/reunioes")
@RequiredArgsConstructor
public class ReuniaoController {

    private final ReuniaoService service;
    private final TranscricaoService transcricaoService;

    @PostMapping
    public ResponseEntity<Void> criar(@RequestBody @Valid ReuniaoRequest request, @AuthenticationPrincipal ConsultorUserDetails userDetails){
        var consultor = userDetails.getConsultor();
        service.criar(request, consultor);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }

    @GetMapping
    public ResponseEntity<Page<ReuniaoResponse>> listarTodos(@PageableDefault(size = 10, sort = {"dataHora"})Pageable pagination, @AuthenticationPrincipal ConsultorUserDetails userDetails){
        var consultor = userDetails.getConsultor();
        var reuniao = service.listar(pagination, consultor);
        return ResponseEntity.ok(reuniao);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ReuniaoResponse> listarPorId(@PathVariable Long id, @AuthenticationPrincipal ConsultorUserDetails userDetails) {
        var consultor = userDetails.getConsultor();
        var reuniao = service.listarPorId(id, consultor);
        return ResponseEntity.ok(reuniao);
    }

    @PutMapping("/{id}")
    public ResponseEntity<ReuniaoResponse> atualizar(@PathVariable Long id, @RequestBody @Valid ReuniaoRequest request, @AuthenticationPrincipal ConsultorUserDetails userDetails){
        var consultor = userDetails.getConsultor();
        var reuniao = service.atualizar(request, consultor, id);
        return ResponseEntity.ok(reuniao);
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
    public ResponseEntity<TranscricaoResponse> enviarTranscricao(@PathVariable Long id, @RequestBody @Valid TranscricaoRequest request, @AuthenticationPrincipal ConsultorUserDetails userDetails){
        var consultor = userDetails.getConsultor();
        var transcricao = transcricaoService.enviar(id, request, consultor);
        return ResponseEntity.ok(transcricao);
    }
}
