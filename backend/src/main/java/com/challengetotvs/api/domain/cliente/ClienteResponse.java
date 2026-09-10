package com.challengetotvs.api.domain.cliente;


public record ClienteResponse(
        Long id,
        String nome,
        String empresa,
        String segmento
) {

    public static ClienteResponse from (Cliente cliente){
        return new ClienteResponse(
                cliente.getId(),
                cliente.getNome(),
                cliente.getEmpresa(),
                cliente.getSegmento()
        );
    }
}
