package com.challengetotvs.api.exception;

import jakarta.persistence.EntityNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;


@RestControllerAdvice
public class GlobalExceptionHandler {

    //Tratando quando não encontrar o que a requisição está pedindo, ele retorna um notFound
    @ExceptionHandler(EntityNotFoundException.class)
    public ResponseEntity<?> tratarErro404(){
        return ResponseEntity.notFound().build();
    }

    //Tratando quando o usuário não enviar uma informação, ele retorna um erro de 400
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<?> tratarErro400(MethodArgumentNotValidException ex){
        var erros = ex.getFieldErrors();
        return ResponseEntity.badRequest().body(erros.stream().map(DadosErroValidacao::new).toList());
    }

    @ExceptionHandler(AnaliseIndisponivelException.class)
    public ResponseEntity<?> tratar503(AnaliseIndisponivelException ex){
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(ex.getMessage());
    }

    private record DadosErroValidacao(String campo, String mensagem){
        public DadosErroValidacao(FieldError error){
            this(error.getField(), error.getDefaultMessage());
        }
    }
}
