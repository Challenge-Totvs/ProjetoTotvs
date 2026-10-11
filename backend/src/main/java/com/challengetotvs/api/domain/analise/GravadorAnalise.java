package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.compromisso.Compromisso;            // E1
import com.challengetotvs.api.domain.compromisso.CompromissoRepository;   // E1
import com.challengetotvs.api.domain.compromisso.PrazoPorRegra;           // E1
import com.challengetotvs.api.domain.reuniao.ReuniaoRepository;
import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import com.challengetotvs.api.domain.transcricao.Transcricao;
import com.challengetotvs.api.exception.AnaliseIndisponivelException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.databind.ObjectMapper;
import com.challengetotvs.api.domain.tema.IncorporadorTemas;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
@Transactional
public class GravadorAnalise {

    private final AnaliseRepository analiseRepository;
    private final ReuniaoRepository reuniaoRepository;
    private final ObjectMapper objectMapper;
    private final IncorporadorTemas incorporadorTemas;
    private final CompromissoRepository compromissoRepository; // E1

    /** E1: o que a gravação produziu, para o AnalisarResponse ("2 temas novos, 2 atualizados, 1 compromisso"). */
    public record Gravado(int novos, int atualizados, int compromissos) {
    }

    public Gravado gravar(Transcricao transcricao, ContratoV3.Resposta bruta,
                          Pseudonimizador pseudonimizador, long duracaoMs) {
        MotorUtilizado motor;
        SentimentoGeral sentimento;
        try {
            motor = MotorUtilizado.de(bruta.motor());
            sentimento = SentimentoGeral.de(bruta.sentimento());
        } catch (IllegalArgumentException | NullPointerException e) {
            throw new AnaliseIndisponivelException("O serviço de análise devolveu um motor ou sentimento desconhecido.", e);
        }

        var resposta = TradutorResposta.restaurar(bruta, pseudonimizador);

        var analise = analiseRepository.findByTranscricaoId(transcricao.getId())
                .orElseGet(() -> new Analise(transcricao));

        analise.setMotor(motor);
        analise.setTentativas(json(resposta.tentativas()));
        analise.setScore(resposta.score());
        analise.setSentimento(sentimento);
        analise.setResumo(resposta.resumo());
        analise.setPapeis(json(resposta.papeis()));
        analise.setInteresse(json(resposta.interesse()));
        analise.setProximosPassos(json(resposta.proximosPassos()));
        analise.setSentimentoSerie(json(resposta.sentimentoSerie()));
        analise.setDescartados(json(resposta.descartados()));
        analise.setEntidades(json(pseudonimizador.mapa()));
        analise.setDuracaoMs(duracaoMs);
        analise.setCriadoEm(LocalDateTime.now());
        analiseRepository.save(analise);

        var reuniao = transcricao.getReuniao();
        reuniao.setStatus(StatusReuniao.ANALISADA);
        reuniaoRepository.save(reuniao);

        var resumo = incorporadorTemas.incorporar(reuniao, resposta);

        // E1: reprocessar uma reunião apaga os compromissos da análise anterior antes de criar os novos
        compromissoRepository.deleteByReuniaoId(reuniao.getId());
        var dataReuniao = reuniao.getDataHora().toLocalDate();
        int criados = 0;
        for (var c : resposta.compromissos()) {
            compromissoRepository.save(Compromisso.builder()
                    .cliente(reuniao.getCliente())
                    .reuniao(reuniao)
                    .turno(c.turno())
                    .texto(c.texto())                                   // já restaurado (nomes reais)
                    .regraPrazo(c.regra())
                    .prazo(PrazoPorRegra.calcular(c.regra(), dataReuniao)) // nulo se não há regra
                    .build());
            criados++;
        }

        return new Gravado(resumo.novos(), resumo.atualizados(), criados);
    }

    private String json(Object valor) {
        return objectMapper.writeValueAsString(valor);
    }


}