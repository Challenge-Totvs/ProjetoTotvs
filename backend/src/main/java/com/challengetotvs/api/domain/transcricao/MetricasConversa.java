package com.challengetotvs.api.domain.transcricao;

import com.challengetotvs.api.domain.transcricao.LeitorTurnos.Turno;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

public final class MetricasConversa {

    private static final String VENDEDOR = "vendedor";
    private static final String CLIENTE = "cliente";

    private MetricasConversa() {
    }

    public record FalaLocutor(int locutor, String papel, int palavras, double percentual) {
    }

    public record Monologo(int palavras, int locutor, String papel, int turno) {
    }

    public record Metricas(
            boolean comPapeis,
            int totalPalavras,
            Double falaVendedor,
            List<FalaLocutor> falaPorLocutor,
            Monologo maiorMonologo,
            Monologo maiorFalaCliente,
            Double trocasPorMinuto,
            Map<String, Integer> perguntas) {
    }

    public static Metricas calcular(List<Turno> turnos, Map<Integer, String> papeis, Integer duracaoMin) {
        boolean comPapeis = !papeis.isEmpty();

        int total = 0;
        Map<Integer, Integer> palavrasPorLocutor = new TreeMap<>();
        int palavrasVendedor = 0;
        Map<String, Integer> perguntas = new LinkedHashMap<>();
        if (comPapeis) {
            perguntas.put(VENDEDOR, 0);
            perguntas.put(CLIENTE, 0);
        }

        List<Monologo> blocos = new ArrayList<>();
        String chaveAtual = null;

        for (Turno t : turnos) {
            int palavras = contarPalavras(t.texto());
            String papel = papelDe(t.locutor(), papeis, comPapeis);
            String chave = comPapeis ? papel : "L" + t.locutor();

            total += palavras;
            palavrasPorLocutor.merge(t.locutor(), palavras, Integer::sum);
            if (VENDEDOR.equals(papel)) {
                palavrasVendedor += palavras;
            }
            if (t.texto().contains("?")) {
                perguntas.merge(chave, 1, Integer::sum);
            }

            if (chave.equals(chaveAtual)) {
                Monologo ultimo = blocos.get(blocos.size() - 1);
                blocos.set(blocos.size() - 1,
                        new Monologo(ultimo.palavras() + palavras, ultimo.locutor(), ultimo.papel(), ultimo.turno()));
            } else {
                blocos.add(new Monologo(palavras, t.locutor(), papel, t.n()));
                chaveAtual = chave;
            }
        }

        final int totalFinal = total;
        List<FalaLocutor> falaPorLocutor = new ArrayList<>();
        palavrasPorLocutor.forEach((locutor, palavras) -> falaPorLocutor.add(new FalaLocutor(
                locutor, papelDe(locutor, papeis, comPapeis), palavras,
                totalFinal == 0 ? 0.0 : (double) palavras / totalFinal)));

        Monologo maior = null;
        Monologo maiorCliente = null;
        for (Monologo b : blocos) {
            if (maior == null || b.palavras() > maior.palavras()) {
                maior = b;
            }
            if (CLIENTE.equals(b.papel()) && (maiorCliente == null || b.palavras() > maiorCliente.palavras())) {
                maiorCliente = b;
            }
        }

        Double falaVendedor = (comPapeis && total > 0) ? (double) palavrasVendedor / total : null;
        Double trocas = (duracaoMin != null && duracaoMin > 0 && !blocos.isEmpty())
                ? (double) (blocos.size() - 1) / duracaoMin : null;

        return new Metricas(comPapeis, total, falaVendedor, falaPorLocutor, maior, maiorCliente, trocas, perguntas);
    }

    private static String papelDe(int locutor, Map<Integer, String> papeis, boolean comPapeis) {
        return comPapeis ? papeis.getOrDefault(locutor, CLIENTE) : null;
    }

    private static int contarPalavras(String texto) {
        String limpo = texto == null ? "" : texto.strip();
        return limpo.isEmpty() ? 0 : limpo.split("\\s+").length;   // sequências sem espaço
    }
}