package com.challengetotvs.api.domain.consultor;

/** Resposta do login: o token JWT e o usuário, para o frontend não precisar chamar /api/me logo depois. */
public record AuthResponse(String token, UsuarioResponse usuario) {
}
