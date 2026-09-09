package com.challengetotvs.api.domain.cliente;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/clientes")
@RequiredArgsConstructor
public class ClienteController {

    private final ClienteService service;

    @PostMapping("/register")
    public ResponseEntity<Void> criar(@RequestBody @Valid ClienteRequest request){
        service.criar(request);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }
}
