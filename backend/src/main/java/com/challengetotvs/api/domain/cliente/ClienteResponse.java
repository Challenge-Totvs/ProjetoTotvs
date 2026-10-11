package com.challengetotvs.api.domain.cliente;

import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import com.challengetotvs.api.domain.tema.Indicadores;
import com.challengetotvs.api.domain.tema.TemaResponse;

import java.time.LocalDateTime;
import java.util.List;

public record ClienteResponse(
        Long id,
        String nome,
        TipoCliente tipo,
        String segmento,
        VendedorRef vendedor,
        List<ContatoResponse> contatos,
        Indicadores indicadores,
        ReuniaoResumo ultimaReuniao,
        ReuniaoResumo ultimaAnalisada,
        ReuniaoResumo proximaReuniao,
        List<TemaResponse> temas
) {

    public record VendedorRef(Long id, String nome) {
    }

    public record ContatoResponse(Long id, String nome, String cargo) {
    }

    public record ReuniaoResumo(Long id, String titulo, LocalDateTime dataHora, Integer duracaoMin,
                                StatusReuniao status, boolean confirmada, String contato,
                                String motor, Integer score) {
    }

    public static ClienteResponse from(Cliente cliente) {
        return from(cliente, Indicadores.zerados(), null, null, null, List.of());
    }

    public static ClienteResponse from(Cliente cliente, Indicadores indicadores, ReuniaoResumo ultima,
                                       ReuniaoResumo ultimaAnalisada, ReuniaoResumo proxima,
                                       List<TemaResponse> temas) {
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
                indicadores, ultima, ultimaAnalisada, proxima, temas
        );
    }
}