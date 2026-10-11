package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.reuniao.ReuniaoRepository;
import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import com.challengetotvs.api.domain.transcricao.Transcricao;
import com.challengetotvs.api.exception.AnaliseIndisponivelException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.databind.ObjectMapper;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
@Transactional
public class GravadorAnalise {

    private final AnaliseRepository analiseRepository;
    private final ReuniaoRepository reuniaoRepository;
    private final ObjectMapper objectMapper;

    public Analise gravar(Transcricao transcricao, ContratoV3.Resposta bruta,
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

        return analise;
    }

    private String json(Object valor) {
        return objectMapper.writeValueAsString(valor);
    }
}