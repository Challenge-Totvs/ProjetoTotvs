package com.challengetotvs.api.domain.tema;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.Map;

public final class ExplicadorTema {

    private static final DateTimeFormatter DIA_MES = DateTimeFormatter.ofPattern("dd/MM");

    private static final Map<String, String> ACOES = Map.ofEntries(
            Map.entry("proposta", "proposta enviada"),
            Map.entry("demonstracao", "demonstração agendada"),
            Map.entry("material", "material técnico enviado"),
            Map.entry("telefone", "retorno por telefone"),
            Map.entry("outra_area", "encaminhada a outra área"),
            Map.entry("outro_o", "outra ação"),
            Map.entry("suporte", "encaminhado ao suporte"),
            Map.entry("retorno", "retorno dado ao cliente"),
            Map.entry("condicao", "condição comercial oferecida"),
            Map.entry("alinhamento", "reunião de alinhamento marcada"),
            Map.entry("outro_r", "outra ação"));

    private static final Map<String, String> CANAIS = Map.of(
            "email", "por e-mail",
            "telefone", "por telefone",
            "whatsapp", "por WhatsApp",
            "presencial", "presencialmente",
            "outro", "por outro canal");

    private static final Map<String, String> MOTIVOS = Map.of(
            "nao_cliente", "não era o cliente falando",
            "fora_contexto", "fora de contexto",
            "tema_errado", "tema errado",
            "outro", "outro");

    private ExplicadorTema() {
    }

    public record Entrada(
            ResultadoSituacao resultado,
            boolean risco,
            boolean oportunidade,
            int janela,
            LocalDate hoje,
            String reuniaoTitulo,
            LocalDate reuniaoData,
            String foraPor, String foraAcao, String foraCanal, LocalDate foraData,
            String naoProcedePor, String naoProcedeMotivo, LocalDate naoProcedeEm) {
    }

    public static String explicar(Entrada e) {
        ResultadoSituacao r = e.resultado();
        long diasUltima = e.reuniaoData() == null ? 0 : ChronoUnit.DAYS.between(e.reuniaoData(), e.hoje());
        String reuniao = "em \"" + e.reuniaoTitulo() + "\" (" + e.reuniaoData().format(DIA_MES) + ")";
        String recorrencia = r.recorrente()
                ? " Citado em " + r.reunioesNaJanela() + " reuniões nos últimos " + e.janela() + " dias."
                : "";

        switch (r.situacao()) {
            case SEM_RETORNO: {
                String base = (e.oportunidade() && !e.risco())
                        ? "Citada " + ha(diasUltima) + ", " + reuniao + ", e ainda sem tratamento."
                        : "Na última reunião em que apareceu, " + ha(diasUltima) + ", " + reuniao + ", ficou sem resposta.";
                String vence = (e.oportunidade() && r.venceEm() != null)
                        ? " Vira oportunidade perdida em " + dias(r.venceEm()) + " se não for tratada."
                        : "";
                return base + vence + recorrencia;
            }
            case OPORTUNIDADE_PERDIDA: {
                long desdePerda = ChronoUnit.DAYS.between(r.perdidaEm(), e.hoje());
                String risco = e.risco() ? " O risco ligado a ela também segue sem resposta." : "";
                return "Citada " + ha(diasUltima) + ", " + reuniao + ", sem tratamento na reunião nem nas seguintes."
                        + " Passou da janela de " + e.janela() + " dias " + ha(desdePerda) + "." + risco;
            }
            case SEM_LEITURA:
                return "O motor que analisou a reunião não identifica quem falou, "
                        + "então não dá para saber se houve resposta.";
            case TRATADO_CONVERSA:
                return "Respondido na própria reunião, " + ha(diasUltima) + ", " + reuniao + "." + recorrencia;
            case TRATADO_FORA:
                return e.foraPor() + " registrou: "
                        + ACOES.getOrDefault(e.foraAcao(), "ação registrada") + ", "
                        + CANAIS.getOrDefault(e.foraCanal(), "por outro canal") + ", em "
                        + e.foraData().format(DIA_MES) + ".";
            case FORA_DE_PAUTA: {
                long semAparecer = ChronoUnit.DAYS.between(r.ultimaAtividade(), e.hoje());
                return "Não aparece há " + dias(semAparecer) + ", mais que a janela de " + e.janela()
                        + ". Sai do resumo e fica no histórico; se voltar, recomeça como tema novo ligado a este.";
            }
            case NAO_PROCEDE: {
                long desde = ChronoUnit.DAYS.between(e.naoProcedeEm(), e.hoje());
                String motivo = e.naoProcedeMotivo() == null ? ""
                        : " Motivo: " + MOTIVOS.getOrDefault(e.naoProcedeMotivo(), e.naoProcedeMotivo()) + ".";
                return "Marcado como não procede por " + e.naoProcedePor() + " " + ha(desde) + "."
                        + motivo + " Vira contraexemplo para as próximas análises.";
            }
            default:
                return "";
        }
    }

    private static String dias(long n) {
        return n == 1 ? "1 dia" : n + " dias";
    }

    private static String ha(long n) {
        return n == 0 ? "hoje" : "há " + dias(n);
    }
}