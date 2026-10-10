package com.challengetotvs.api.exception;

import jakarta.persistence.EntityNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {


    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ErroApi> tratarApi(ApiException ex) {
        return resposta(ex.getStatus(), ex.getCodigo(), ex.getMessage());
    }


    @ExceptionHandler(EntityNotFoundException.class)
    public ResponseEntity<ErroApi> tratar404(EntityNotFoundException ex) {
        return resposta(HttpStatus.NOT_FOUND, "nao_encontrado", "Recurso não encontrado.");
    }


    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErroApi> tratar400(MethodArgumentNotValidException ex) {
        var mensagem = ex.getFieldErrors().stream()
                .map(e -> e.getField() + ": " + e.getDefaultMessage())
                .collect(Collectors.joining("; "));
        return resposta(HttpStatus.BAD_REQUEST, "validacao", mensagem);
    }


    @ExceptionHandler(BadCredentialsException.class)
    public ResponseEntity<ErroApi> tratar401(BadCredentialsException ex) {
        return resposta(HttpStatus.UNAUTHORIZED, "credenciais_invalidas", "E-mail ou senha incorretos.");
    }


    @ExceptionHandler(AnaliseIndisponivelException.class)
    public ResponseEntity<ErroApi> tratar503(AnaliseIndisponivelException ex) {
        return resposta(HttpStatus.SERVICE_UNAVAILABLE, "analise_indisponivel", ex.getMessage());
    }

    private ResponseEntity<ErroApi> resposta(HttpStatus status, String codigo, String mensagem) {
        return ResponseEntity.status(status).body(new ErroApi(codigo, mensagem));
    }
}