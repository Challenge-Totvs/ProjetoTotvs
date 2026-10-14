package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.tema.NaoProcedeDoCliente.Trecho;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class NaoProcedeDoClienteTest {

    private static final long CLIENTE_ID = 7L;

    private final EventoTemaRepository eventos = mock(EventoTemaRepository.class);
    private final CitacaoRepository citacoes = mock(CitacaoRepository.class);
    private final NaoProcedeDoCliente naoProcede = new NaoProcedeDoCliente(eventos, citacoes);

    @Test
    void semMarcacaoNaoHaTrecho() {
        when(eventos.findByTemaClienteIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(CLIENTE_ID, TipoEvento.NAO_PROCEDE))
                .thenReturn(List.of());

        assertThat(naoProcede.doCliente(CLIENTE_ID)).isEmpty();
    }

    @Test
    void motivoVazioViraOutroETemaRepetidoEntraUmaVez() {
        Tema tema = tema(31L, "preco_objecao");
        when(eventos.findByTemaClienteIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(CLIENTE_ID, TipoEvento.NAO_PROCEDE))
                .thenReturn(List.of(evento(tema, null, agora()), evento(tema, "tema_errado", agora().minusDays(1))));
        when(citacoes.findByTemaIdOrderByReuniaoDataHoraAsc(31L))
                .thenReturn(List.of(citacao(tema, "O valor ficou salgado.", agora().minusDays(2))));

        assertThat(naoProcede.doCliente(CLIENTE_ID))
                .containsExactly(new Trecho(31L, "preco_objecao", "O valor ficou salgado.", "outro"));
    }

    @Test
    void usaACitacaoQueValiaNaHoraDaMarcacao() {
        Tema tema = tema(31L, "renovacao");
        LocalDateTime marcado = agora().minusDays(5);
        var evento = evento(tema, "fora_contexto", marcado);
        when(citacoes.findByTemaIdOrderByReuniaoDataHoraAsc(31L)).thenReturn(List.of(
                citacao(tema, "trecho antigo", marcado.minusDays(10)),
                citacao(tema, "trecho marcado", marcado.minusHours(1)),
                citacao(tema, "trecho de depois", marcado.plusDays(2))));

        assertThat(naoProcede.trecho(evento)).contains("trecho marcado");
    }

    @Test
    void semCitacaoAnteriorUsaAUltimaDeTodas() {
        Tema tema = tema(31L, "renovacao");
        LocalDateTime marcado = agora().minusDays(5);
        var evento = evento(tema, "fora_contexto", marcado);
        when(citacoes.findByTemaIdOrderByReuniaoDataHoraAsc(31L)).thenReturn(List.of(
                citacao(tema, "primeira depois da marcacao", marcado.plusDays(1)),
                citacao(tema, "ultima de todas", marcado.plusDays(3))));

        assertThat(naoProcede.trecho(evento)).contains("ultima de todas");
    }

    @Test
    void temaSemCitacaoFicaDeFora() {
        Tema tema = tema(31L, "renovacao");
        when(eventos.findByTemaClienteIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(CLIENTE_ID, TipoEvento.NAO_PROCEDE))
                .thenReturn(List.of(evento(tema, "outro", agora())));
        when(citacoes.findByTemaIdOrderByReuniaoDataHoraAsc(31L)).thenReturn(List.of());

        assertThat(naoProcede.doCliente(CLIENTE_ID)).isEmpty();
    }

    @Test
    void paraEmCinquentaTemas() {
        var lista = new ArrayList<EventoTema>();
        for (long id = 1; id <= 60; id++) {
            lista.add(evento(tema(id, "renovacao"), "outro", agora().minusMinutes(id)));
        }
        when(eventos.findByTemaClienteIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(CLIENTE_ID, TipoEvento.NAO_PROCEDE))
                .thenReturn(lista);
        when(citacoes.findByTemaIdOrderByReuniaoDataHoraAsc(anyLong()))
                .thenAnswer(inv -> List.of(citacao(tema(inv.getArgument(0), "renovacao"), "trecho", agora().minusDays(90))));

        var trechos = naoProcede.doCliente(CLIENTE_ID);

        assertThat(trechos).hasSize(NaoProcedeDoCliente.MAXIMO);
        assertThat(trechos.get(0).temaId()).isEqualTo(1L);   // mantém a ordem do mais novo ao mais antigo
    }

    private static LocalDateTime agora() {
        return LocalDateTime.of(2026, 10, 13, 12, 0);
    }

    private static Tema tema(Long id, String padrao) {
        Tema t = new Tema();
        t.setId(id);
        t.setPadrao(new Padrao(padrao, padrao, TipoPadrao.RISCO));
        return t;
    }

    private static EventoTema evento(Tema tema, String motivo, LocalDateTime criadoEm) {
        EventoTema e = EventoTema.builder().tema(tema).tipo(TipoEvento.NAO_PROCEDE).motivo(motivo).build();
        e.setCriadoEm(criadoEm);
        return e;
    }

    private static Citacao citacao(Tema tema, String texto, LocalDateTime criadoEm) {
        Citacao c = Citacao.builder().tema(tema).turno(1).texto(texto).build();
        c.setCriadoEm(criadoEm);
        return c;
    }
}
