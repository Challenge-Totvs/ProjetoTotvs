package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.analise.ContratoV3.CompromissoResposta;
import com.challengetotvs.api.domain.analise.ContratoV3.Descartado;
import com.challengetotvs.api.domain.analise.ContratoV3.Interesse;
import com.challengetotvs.api.domain.analise.ContratoV3.Resposta;
import com.challengetotvs.api.domain.analise.ContratoV3.TemaResposta;

public final class TradutorResposta {

    private TradutorResposta() {
    }

    public static Resposta restaurar(Resposta r, Pseudonimizador p) {
        return new Resposta(
                r.motor(), r.tentativas(), r.score(), r.sentimento(), r.papeis(),
                p.restaurar(r.resumo()),
                r.interesse().stream()
                        .map(i -> new Interesse(p.restaurar(i.texto()), i.turno(), p.restaurar(i.citacao())))
                        .toList(),
                r.proximosPassos().stream().map(p::restaurar).toList(),
                r.temas().stream()
                        .map(t -> new TemaResposta(t.padrao(), p.restaurar(t.titulo()), t.tipos(),
                                t.turno(), t.turnoFim(), t.tratado(), p.restaurar(t.texto())))
                        .toList(),
                r.compromissos().stream()
                        .map(c -> new CompromissoResposta(c.turno(), p.restaurar(c.texto()), c.regra()))
                        .toList(),
                r.sentimentoSerie(),
                r.descartados().stream()
                        .map(d -> new Descartado(p.restaurar(d.texto()), d.motivo()))
                        .toList());
    }
}