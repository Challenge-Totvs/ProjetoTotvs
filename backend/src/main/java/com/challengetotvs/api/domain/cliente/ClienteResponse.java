package com.challengetotvs.api.domain.cliente;

import com.challengetotvs.api.domain.reuniao.StatusReuniao;   // enum da reunião (agendada, aguardando, analisada)
import com.challengetotvs.api.domain.tema.Indicadores;        // indicadores do cliente (J10a)
import com.challengetotvs.api.domain.tema.TemaResponse;       // tema já calculado

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
        List<TemaResponse> temas,
        List<ReuniaoItem> reunioes,
        List<Object> compromissos
) {

    public record VendedorRef(Long id, String nome) {
    }

    public record ContatoResponse(Long id, String nome, String cargo) {
    }

    public record ReuniaoResumo(Long id, String titulo, LocalDateTime dataHora, Integer duracaoMin,
                                StatusReuniao status, boolean confirmada, String contato,
                                String motor, Integer score) {
    }

    public record ReuniaoItem(Long id, String titulo, LocalDateTime dataHora, StatusReuniao status,
                              boolean confirmada, String contato, String motor, Integer score,
                              Integer turnos) {   // turnos nulo se ainda não há transcrição
    }

    public static ClienteResponse from(Cliente cliente) {
        return from(cliente, Indicadores.zerados(), null, null, null, List.of(), List.of(), List.of());
    }

    public static ClienteResponse from(Cliente cliente, Indicadores indicadores, ReuniaoResumo ultima,
                                       ReuniaoResumo ultimaAnalisada, ReuniaoResumo proxima,
                                       List<TemaResponse> temas, List<ReuniaoItem> reunioes,
                                       List<Object> compromissos) {
        var dono = cliente.getVendedor();
        return new ClienteResponse(
                cliente.getId(),
                cliente.getNome(),
                cliente.getTipo(),
                cliente.getSegmento(),
                dono == null ? null : new VendedorRef(dono.getId(), dono.getNome()),
                cliente.getContatos().stream()
                        .map(c -> new ContatoResponse(c.getId(), c.getNome(), c.getCargo()))
                        .toList(),
                indicadores, ultima, ultimaAnalisada, proxima, temas, reunioes, compromissos
        );
    }
}