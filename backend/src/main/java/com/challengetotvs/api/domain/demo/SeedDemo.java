package com.challengetotvs.api.domain.demo;

import com.challengetotvs.api.domain.analise.ContratoV3;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.util.List;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public record SeedDemo(List<UsuarioSeed> usuarios, List<ClienteSeed> clientes,
                       List<ReuniaoSeed> reunioes, List<TemaSeed> temas,
                       List<CompromissoSeed> compromissos) {   // E1

    public record UsuarioSeed(String email, String senha, String nome, String perfil, String vendedorId) {
    }

    public record ContatoSeed(String nome, String cargo) {
    }

    public record ClienteSeed(String id, String nome, String tipo, String segmento, String vendedor,
                              List<ContatoSeed> contatos) {
    }

    public record Fala(int loc, String texto) {
    }

    public record ReuniaoSeed(String id, String cliente, int d, String h, String titulo, String contato,
                              String status, boolean confirmada, Integer duracaoMin, Integer score,
                              String sentimento, String resumo, Map<String, String> papeis,
                              List<ContratoV3.Interesse> interesse, List<String> proximosPassos,
                              List<ContratoV3.Descartado> descartados, List<double[]> sentimentoSerie,
                              List<Fala> transcricao) {   // nulo em reunião sem transcrição
    }

    public record CitacaoSeed(String reuniao, int turno, boolean tratado, String texto) {
    }

    public record NaoProcedeSeed(String motivo, String por, int d, String h) {
    }

    public record TemaSeed(String id, String cliente, String padrao, String titulo, List<String> tipos,
                           List<CitacaoSeed> citacoes, NaoProcedeSeed naoProcede) {
    }

    public record CompromissoSeed(String id, String cliente, String reuniao, int turno, String texto,
                                  String regra, Boolean cumprido) {
    }
}