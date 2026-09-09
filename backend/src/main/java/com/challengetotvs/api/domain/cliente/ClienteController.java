package com.challengetotvs.api.domain.cliente;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/clientes")
@RequiredArgsConstructor
public class ClienteController {

    private final ClienteService service;

    @PostMapping("/register")
    public ResponseEntity<Void> create(@RequestBody @Valid ClienteRequest request){
        service.criar(request);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }

    @GetMapping
    public ResponseEntity<Page<ClienteResponse>> listall(@PageableDefault(size = 10, sort = {"nome"})Pageable pagination){
        var cliente = service.listar(pagination);
        return ResponseEntity.ok(cliente);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ClienteResponse> listid(@PathVariable Long id){
        var cliente = service.listarPorId(id);
        return ResponseEntity.ok(cliente);
    }
}
