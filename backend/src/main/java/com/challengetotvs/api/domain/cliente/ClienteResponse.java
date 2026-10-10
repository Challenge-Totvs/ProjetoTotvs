package com.challengetotvs.api.domain.cliente;

import java.util.List;

public record ClienteResponse(
        Long id,
        String nome,
        TipoCliente tipo,
        String segmento,
        VendedorRef vendedor,
        List<ContatoResponse> contatos,
        Indicadores indicadores,
        Object ultimaReuniao,
        Object ultimaAnalisada,
        Object proximaReuniao,
        List<Object> temasEmPauta
) {

    public record VendedorRef(Long id, String nome) {
    }

    public record ContatoResponse(Long id, String nome, String cargo) {
    }

    public record Indicadores(
            int emPauta, int riscosSemRetorno, int riscosRecorrentes, int oportPerdidas,
            int oportSemRetorno, int tratadosConversa, int tratadosFora, int foraDePauta,
            int naoProcede, int recorrentes, int atencao
    ) {
        public static Indicadores zerados() {
            return new Indicadores(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
        }
    }

    public static ClienteResponse from(Cliente cliente) {
        var dono = cliente.getVendedor();
        return new ClienteResponse(
                cliente.getId(),
                cliente.getNome(),
                cliente.getTipo(),
                cliente.getSegmento(),
                dono == null ? null : new VendedorRef(dono.getId(), dono.getNome()), // cliente antigo pode não ter dono
                cliente.getContatos().stream()
                        .map(c -> new ContatoResponse(c.getId(), c.getNome(), c.getCargo()))
                        .toList(),
                Indicadores.zerados(),
                null, null, null,
                List.of()
        );
    }
}