package com.challengetotvs.api.domain.transcricao;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

public final class LeitorTurnos {

    private static final Pattern MARCACAO =
            Pattern.compile("^\\s*\\[LOCUTOR\\s*(\\d{1,9})\\]\\s*:?\\s*(.*)$", Pattern.CASE_INSENSITIVE);

    private LeitorTurnos() {
    }

    public record Turno(int n, int locutor, String texto) {
    }

    public static List<Turno> ler(String transcricao) {
        if (transcricao == null) {
            return List.of();
        }
        var linhas = transcricao.replace("\r\n", "\n").replace('\r', '\n').split("\n", -1);

        var locutores = new ArrayList<Integer>();
        var textos = new ArrayList<String>();

        for (var linha : linhas) {
            var m = MARCACAO.matcher(linha);
            if (m.matches()) {
                locutores.add(Integer.parseInt(m.group(1)));
                textos.add(m.group(2).strip());
            } else if (!linha.isBlank() && !textos.isEmpty()) {
                var ultimo = textos.size() - 1;
                textos.set(ultimo, (textos.get(ultimo) + " " + linha.strip()).strip());
            }
        }

        var turnos = new ArrayList<Turno>();
        for (int i = 0; i < textos.size(); i++) {
            if (!textos.get(i).isEmpty()) {
                turnos.add(new Turno(turnos.size() + 1, locutores.get(i), textos.get(i)));
            }
        }
        return turnos;
    }
}