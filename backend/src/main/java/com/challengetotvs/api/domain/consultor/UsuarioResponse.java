package com.challengetotvs.api.domain.consultor;

/**
 * O usuário logado, no formato que o frontend espera (types/api.ts, interface Usuario).
 * É devolvido no login e em GET /api/me.
 */
public record UsuarioResponse(
        Long id,
        String nome,
        String email,
        String perfil,
        String time,
        Gestor gestor
) {

    /** Gestor do time, usado no "Avisar gestor". */
    public record Gestor(Long id, String nome) {
    }

    /**
     * Converte o Consultor do banco no formato do frontend.
     * ROLE "GESTOR" vira perfil "gestor"; qualquer outra vira "vendedor".
     * Enquanto não existir a tabela de times, o time é fixo e o gestor é nulo.
     */
    public static UsuarioResponse de(Consultor consultor) {
        var perfil = "GESTOR".equals(consultor.getRole()) ? "gestor" : "vendedor";
        return new UsuarioResponse(
                consultor.getId(),
                consultor.getNome(),
                consultor.getEmail(),
                perfil,
                "Comercial",
                null
        );
    }
}
