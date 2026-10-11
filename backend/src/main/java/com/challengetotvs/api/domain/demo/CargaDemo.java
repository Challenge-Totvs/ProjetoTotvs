package com.challengetotvs.api.domain.demo;

import com.challengetotvs.api.domain.analise.*;
import com.challengetotvs.api.domain.cliente.Cliente;
import com.challengetotvs.api.domain.cliente.ClienteRepository;
import com.challengetotvs.api.domain.cliente.TipoCliente;
import com.challengetotvs.api.domain.compromisso.Compromisso;          // E1
import com.challengetotvs.api.domain.compromisso.CompromissoRepository; // E1
import com.challengetotvs.api.domain.compromisso.PrazoPorRegra;         // E1
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.consultor.ConsultorRepository;
import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.reuniao.ReuniaoRepository;
import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import com.challengetotvs.api.domain.tema.*;
import com.challengetotvs.api.domain.transcricao.Transcricao;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import tools.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.ZoneId;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Collectors;


@Slf4j
@Component
@Profile("demo")
@RequiredArgsConstructor
public class CargaDemo implements ApplicationRunner {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");
    private static final String CONTA_MARCA = "kelwin.bastos@insightcall.com";

    private final CargaPadroes cargaPadroes;
    private final ConsultorRepository consultorRepository;
    private final ClienteRepository clienteRepository;
    private final ReuniaoRepository reuniaoRepository;
    private final TranscricaoRepository transcricaoRepository;
    private final AnaliseRepository analiseRepository;
    private final PadraoRepository padraoRepository;
    private final TemaRepository temaRepository;
    private final CitacaoRepository citacaoRepository;
    private final EventoTemaRepository eventoTemaRepository;
    private final CompromissoRepository compromissoRepository; // E1
    private final PasswordEncoder passwordEncoder;
    private final ObjectMapper objectMapper;
    private final PlatformTransactionManager transactionManager;

    @Override
    public void run(ApplicationArguments args) {
        cargaPadroes.run();

        if (consultorRepository.findByEmail(CONTA_MARCA).isPresent()) {
            log.info("Carga da demo já feita (a conta {} existe). Nada a fazer.", CONTA_MARCA);
            return;
        }
        var seed = lerSeed();
        new TransactionTemplate(transactionManager).executeWithoutResult(status -> carregar(seed));
        log.info("Carga da demo concluída: {} clientes, {} reuniões, {} temas, {} compromissos.",
                seed.clientes().size(), seed.reunioes().size(), seed.temas().size(),
                seed.compromissos() == null ? 0 : seed.compromissos().size());
    }

    private SeedDemo lerSeed() {
        try (var in = getClass().getResourceAsStream("/demo/seed.json")) {
            if (in == null) {
                throw new IllegalStateException("Falta src/main/resources/demo/seed.json (rode scripts/gerar-seed.mjs).");
            }
            return objectMapper.readValue(in, SeedDemo.class);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    private void carregar(SeedDemo seed) {
        LocalDate hoje = LocalDate.now(FUSO);

        Map<String, Consultor> vendedores = new HashMap<>();   // "kb" -> Kelwin ...
        for (var u : seed.usuarios()) {
            var role = "gestor".equals(u.perfil()) ? "GESTOR" : "CONSULTOR";
            var consultor = consultorRepository.save(
                    new Consultor(u.nome(), u.email(), passwordEncoder.encode(u.senha()), role));
            if (u.vendedorId() != null) {
                vendedores.put(u.vendedorId(), consultor);
            }
        }

        Map<String, Cliente> clientes = new HashMap<>();
        for (var c : seed.clientes()) {
            var cliente = Cliente.builder()
                    .nome(c.nome())
                    .tipo(c.tipo() == null ? null : TipoCliente.valueOf(c.tipo().toUpperCase(Locale.ROOT)))
                    .segmento(c.segmento())
                    .vendedor(vendedores.get(c.vendedor()))
                    .build();
            c.contatos().forEach(ct -> cliente.adicionarContato(ct.nome(), ct.cargo()));
            clientes.put(c.id(), clienteRepository.save(cliente));
        }

        Map<String, Reuniao> reunioes = new HashMap<>();
        for (var r : seed.reunioes()) {
            var cliente = clientes.get(r.cliente());
            var contato = cliente.getContatos().stream()
                    .filter(c -> c.getNome().equals(r.contato()))
                    .findFirst().orElse(null);
            var reuniao = Reuniao.builder()
                    .consultor(cliente.getVendedor())
                    .cliente(cliente)
                    .contato(contato)
                    .dataHora(hoje.plusDays(r.d()).atTime(LocalTime.parse(r.h())))
                    .titulo(r.titulo())
                    .duracaoMin(r.duracaoMin())
                    .status(statusDe(r.status()))
                    .build();
            reuniao.setConfirmada(r.confirmada());
            reuniao = reuniaoRepository.save(reuniao);
            reunioes.put(r.id(), reuniao);
            if (r.transcricao() != null) {
                gravarAnalise(reuniao, r);
            }
        }

        for (var t : seed.temas()) {
            var padrao = padraoRepository.findById(t.padrao())
                    .orElseThrow(() -> new IllegalStateException("Padrão ausente: " + t.padrao()));
            var tema = temaRepository.save(Tema.builder()
                    .cliente(clientes.get(t.cliente()))
                    .padrao(padrao)
                    .titulo(t.titulo())
                    .risco(t.tipos().contains("risco"))
                    .oportunidade(t.tipos().contains("oportunidade"))
                    .build());
            for (var c : t.citacoes()) {
                citacaoRepository.save(Citacao.builder()
                        .tema(tema)
                        .reuniao(reunioes.get(c.reuniao()))
                        .turno(c.turno())
                        .tratado(c.tratado())
                        .texto(c.texto())
                        .build());
            }
            if (t.naoProcede() != null) {
                var np = t.naoProcede();
                var evento = EventoTema.builder()
                        .tema(tema).tipo(TipoEvento.NAO_PROCEDE).motivo(np.motivo())
                        .por(vendedores.get(np.por()))
                        .build();
                evento.setCriadoEm(hoje.plusDays(np.d()).atTime(LocalTime.parse(np.h())));
                eventoTemaRepository.save(evento);
            }
        }

        // E1: compromissos. O prazo vem da regra e da data da reunião, igual ao que a análise faz de verdade.
        if (seed.compromissos() != null) {
            for (var cp : seed.compromissos()) {
                var reuniaoDoCompromisso = reunioes.get(cp.reuniao());
                var compromisso = Compromisso.builder()
                        .cliente(clientes.get(cp.cliente()))
                        .reuniao(reuniaoDoCompromisso)
                        .turno(cp.turno())
                        .texto(cp.texto())
                        .regraPrazo(cp.regra())
                        .prazo(PrazoPorRegra.calcular(cp.regra(), reuniaoDoCompromisso.getDataHora().toLocalDate()))
                        .build();
                if (Boolean.TRUE.equals(cp.cumprido())) {
                    // cumprido há 2 dias, pelo dono do cliente: aparece no Início (cumpridos há até 3 dias)
                    compromisso.cumprir(reuniaoDoCompromisso.getConsultor(), hoje.minusDays(2).atTime(10, 0));
                }
                compromissoRepository.save(compromisso);
            }
        }
    }

    private void gravarAnalise(Reuniao reuniao, SeedDemo.ReuniaoSeed r) {
        var conteudo = r.transcricao().stream()
                .map(f -> "[LOCUTOR " + f.loc() + "]: " + f.texto())
                .collect(Collectors.joining("\n"));
        int locutores = (int) r.transcricao().stream().map(SeedDemo.Fala::loc).distinct().count();

        var transcricao = transcricaoRepository.save(Transcricao.builder()
                .reuniao(reuniao).conteudo(conteudo).formatoOrigem("COLADO")
                .hashTexto(sha256(conteudo)).caracteres(conteudo.length())
                .turnos(r.transcricao().size()).locutores(locutores)
                .build());

        var analise = new Analise(transcricao);
        analise.setMotor(MotorUtilizado.LLM1);
        analise.setTentativas(json(List.of(new ContratoV3.Tentativa("llm1", true))));
        analise.setScore(r.score());
        analise.setSentimento(SentimentoGeral.de(r.sentimento()));
        analise.setResumo(r.resumo());
        analise.setPapeis(json(r.papeis()));
        analise.setInteresse(json(r.interesse()));
        analise.setProximosPassos(json(r.proximosPassos()));
        analise.setSentimentoSerie(json(r.sentimentoSerie()));
        analise.setDescartados(json(r.descartados()));
        analise.setEntidades("{}");
        analise.setDuracaoMs(4000L);
        analiseRepository.save(analise);
    }

    private static StatusReuniao statusDe(String status) {
        return switch (status) {
            case "agendada" -> StatusReuniao.AGENDADA;
            case "aguardando" -> StatusReuniao.REALIZADA;
            case "analisada" -> StatusReuniao.ANALISADA;
            default -> throw new IllegalStateException("Status desconhecido na demo: " + status);
        };
    }

    private String json(Object valor) {
        return objectMapper.writeValueAsString(valor);
    }

    private static String sha256(String texto) {
        try {
            var digest = MessageDigest.getInstance("SHA-256").digest(texto.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 indisponível", e);
        }
    }
}