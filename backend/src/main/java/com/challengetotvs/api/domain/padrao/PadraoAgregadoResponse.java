package com.challengetotvs.api.domain.padrao;

import java.time.LocalDate;
import java.util.List;


public record PadraoAgregadoResponse(
        String padrao,
        String nome,
        String tipo,
        int total,
        int naoProcede,
        double taxaNaoProcede,
        int clientes,
        int semRetorno,
        int perdidas,
        int recorrentes,
        Double taxaConversa,
        List<Integer> terco,
        List<List<Object>> porVendedor,
        List<List<Object>> porSegmento,
        List<List<Object>> motivos,
        List<Amostra> amostra) {

    public record ClienteRef(Long id, String nome) {
    }

    public record Amostra(
            Long reuniaoId,
            String reuniaoTitulo,
            LocalDate reuniaoData,
            int turno,
            Boolean tratado,
            String texto,
            boolean conferida,
            Integer locutor,
            String papel,
            List<Object> contexto,
            Long temaId,
            ClienteRef cliente,
            String vendedorNome) {
    }
}