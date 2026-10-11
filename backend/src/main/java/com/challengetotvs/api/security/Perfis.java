package com.challengetotvs.api.security;

import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.exception.ApiException;
import org.springframework.http.HttpStatus;

public final class Perfis {

    private Perfis() {
    }

    public static boolean ehGestor(Consultor consultor) {
        return "GESTOR".equals(consultor.getRole());
    }

    public static void exigirGestor(Consultor consultor) {
        if (!ehGestor(consultor)) {
            throw new ApiException(HttpStatus.FORBIDDEN, "sem_permissao", "Só a gestão acessa esta área.");
        }
    }
}