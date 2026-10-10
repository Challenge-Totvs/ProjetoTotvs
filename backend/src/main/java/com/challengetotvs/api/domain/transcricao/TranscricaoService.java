package com.challengetotvs.api.domain.transcricao;

import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.reuniao.ReuniaoRepository;
import com.challengetotvs.api.exception.ApiException;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDate;
import java.util.HexFormat;

@Service
@RequiredArgsConstructor
@Transactional
public class TranscricaoService {

    private static final int MINIMO_CARACTERES = 80;
    private static final int MAXIMO_CARACTERES = 200_000;

    private final TranscricaoRepository transcricaoRepository;
    private final ReuniaoRepository reuniaoRepository;

    public EnviarTranscricaoResponse enviar(Long reuniaoId, TranscricaoRequest request, Consultor consultor) {
        var reuniao = reuniaoRepository.findById(reuniaoId)
                .filter(r -> r.pertenceA(consultor))
                .orElseThrow(() -> new EntityNotFoundException("Reunião não encontrada!"));

        if (reuniao.getDataHora().toLocalDate().isAfter(LocalDate.now())) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "reuniao_futura",
                    "Esta reunião ainda não aconteceu. Envie a transcrição depois dela.");
        }

        var texto = normalizar(request.conteudo());

        if (texto.length() < MINIMO_CARACTERES) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "transcricao_curta",
                    "A transcrição precisa ter pelo menos " + MINIMO_CARACTERES + " caracteres.");
        }
        if (texto.length() > MAXIMO_CARACTERES) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "transcricao_longa",
                    "A transcrição passa do limite de " + MAXIMO_CARACTERES + " caracteres.");
        }

        var turnos = LeitorTurnos.ler(texto);
        if (turnos.isEmpty()) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "sem_locutor",
                    "Não encontrei marcações [LOCUTOR n] no texto. Cada fala precisa começar com elas.");
        }

        var hash = hashDe(texto);
        transcricaoRepository.findFirstByHashTextoAndReuniaoClienteId(hash, reuniao.getCliente().getId())
                .ifPresent(existente -> {
                    throw new ApiException(HttpStatus.CONFLICT, "transcricao_duplicada",
                            "Esta transcrição já foi enviada para este cliente (reunião "
                                    + existente.getReuniao().getId() + ").");
                });

        if (transcricaoRepository.existsByReuniaoId(reuniaoId)) {
            throw new ApiException(HttpStatus.CONFLICT, "reuniao_com_transcricao",
                    "Esta reunião já tem uma transcrição.");
        }

        int locutores = (int) turnos.stream().map(LeitorTurnos.Turno::locutor).distinct().count();

        var transcricao = new Transcricao(reuniao, texto, request.formatoOrigem(),
                hash, texto.length(), turnos.size(), locutores);
        transcricaoRepository.save(transcricao);

        return new EnviarTranscricaoResponse(transcricao.getId(), texto.length(), turnos.size(), locutores);
    }

    private String normalizar(String conteudo) {
        return conteudo.replace("\r\n", "\n").replace('\r', '\n').strip();
    }

    private String hashDe(String texto) {
        var semEspacosExtras = texto.replaceAll("\\s+", " ");
        try {
            var digest = MessageDigest.getInstance("SHA-256")
                    .digest(semEspacosExtras.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);   // 32 bytes viram 64 caracteres hexadecimais
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 indisponível", e);   // todo JDK tem; nunca deve acontecer
        }
    }
}