package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import tools.jackson.databind.ObjectMapper;

@Service
@RequiredArgsConstructor
public class AnaliseService {

    private final TranscricaoRepository transcricaoRepository;
    private final AnaliseRepository analiseRepository;
    private final AnaliseStrategy strategy;
    private final ObjectMapper objectMapper;

    public ResultadoAnalise analisar(Long transcricaoId, Consultor consultor){
        var transcricao = transcricaoRepository.findById(transcricaoId)
                    .orElseThrow(() -> new EntityNotFoundException("Transcrição não encontrada"));

        if(!transcricao.getReuniao().pertenceA(consultor)){
            throw new AccessDeniedException("Você não tem permissão para acessar essa transcrição!");
        }

        var resultado = strategy.analisar(transcricao.getConteudo());

        String interesse = objectMapper.writeValueAsString(resultado.pontosInteresse());
        String desinteresse = objectMapper.writeValueAsString(resultado.pontosDesinteresse());
        String oportunidades = objectMapper.writeValueAsString(resultado.oportunidadesVenda());
        SentimentoGeral sentimento = resultado.sentimentoGeral();

        var existente = analiseRepository.findByTranscricaoId(transcricaoId);

        if (existente.isPresent()) {
            var analise = existente.get();
            analise.atualizar(interesse, desinteresse, oportunidades, resultado.scoreEngajamento(),
                    sentimento, resultado.recomendacaoProximosPassos(), resultado.motorUtilizado());
            analiseRepository.save(analise);
        } else {
            analiseRepository.save(Analise.builder()
                    .transcricao(transcricao)
                    .pontosInteresse(interesse)
                    .pontosDesinteresse(desinteresse)
                    .oportunidadesVenda(oportunidades)
                    .scoreEngajamento(resultado.scoreEngajamento())
                    .sentimentoGeral(sentimento)
                    .recomendacaoProximosPassos(resultado.recomendacaoProximosPassos())
                    .motorUtilizado(resultado.motorUtilizado())
                    .build());
        }

        return resultado;
    }
}
