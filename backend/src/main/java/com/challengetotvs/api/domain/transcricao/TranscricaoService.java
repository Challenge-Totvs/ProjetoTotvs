package com.challengetotvs.api.domain.transcricao;

import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.reuniao.ReuniaoRepository;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class TranscricaoService {

    private final TranscricaoRepository transcricaoRepository;
    private final ReuniaoRepository reuniaoRepository;

    public TranscricaoResponse enviar(Long id, TranscricaoRequest request, Consultor consultor){
        var reuniao = reuniaoRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Reunião não encontrada!"));

        if(!reuniao.pertenceA(consultor)){
            throw new AccessDeniedException("Você não tem permissão para acessar essa reunião!");
        }

        var transcricao = new Transcricao(
                reuniao,
                request.conteudo(),
                request.formatoOrigem()
        );
        transcricaoRepository.save(transcricao);
        return TranscricaoResponse.from(transcricao);
    }
}
