package com.challengetotvs.api.exception;

public class AnaliseIndisponivelException extends RuntimeException{

    public AnaliseIndisponivelException(String mensagem){
       super(mensagem);
    }

    public AnaliseIndisponivelException(String mensagem, Throwable causa){
        super(mensagem, causa);
    }


}
