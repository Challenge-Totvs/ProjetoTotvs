package com.challengetotvs.api.domain.evidencia;

import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.evidencia.ClienteEvidencias.Trecho;
import com.challengetotvs.api.domain.evidencia.EvidenciaResponse.Evidencia;
import com.challengetotvs.api.domain.evidencia.HistoricoDoCliente.Turno;
import com.challengetotvs.api.exception.ApiException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;

/** "Buscar no histórico do cliente". SEM @Transactional: a espera pelo Python não pode segurar o banco. */
@Service
@RequiredArgsConstructor
public class EvidenciaService {

    static final int MAXIMO_CONSULTA = 500;   // evidencias.md §2
    static final String AVISO_SEM_TRANSCRICAO = "Este cliente ainda não tem transcrições para buscar.";
    static final String AVISO_INDISPONIVEL = "A busca está indisponível no momento. Tente de novo em instantes.";

    private final HistoricoDoCliente historicoDoCliente;
    private final ClienteEvidencias clienteEvidencias;

    public EvidenciaResponse buscar(Long clienteId, String consulta, Consultor usuario) {
        if (consulta == null || consulta.isBlank()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "consulta_vazia", "Digite o que você quer buscar.");
        }
        String limpa = consulta.strip();
        if (limpa.length() > MAXIMO_CONSULTA) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "consulta_longa",
                    "A busca aceita no máximo " + MAXIMO_CONSULTA + " caracteres.");
        }

        var historico = historicoDoCliente.carregar(clienteId, usuario);
        if (historico.turnos().isEmpty()) {
            return EvidenciaResponse.vazia(AVISO_SEM_TRANSCRICAO);
        }

        var pseudo = historico.pseudonimizador();
        var originais = new HashMap<String, Turno>();
        var trechos = new ArrayList<Trecho>();
        for (var turno : historico.turnos()) {
            originais.put(turno.id(), turno);
            trechos.add(new Trecho(turno.id(), cortar(pseudo.pseudonimizar(turno.texto()))));
        }

        var achados = clienteEvidencias.buscar(cortar(pseudo.pseudonimizar(limpa)), trechos);
        if (achados.isEmpty()) {
            return EvidenciaResponse.vazia(AVISO_INDISPONIVEL);
        }
        // o texto que volta é o turno original: o Python só viu os pseudônimos
        var evidencias = achados.get().stream()
                .filter(a -> originais.containsKey(a.id()))
                .map(a -> {
                    var t = originais.get(a.id());
                    return new Evidencia(t.texto(), t.reuniaoId(), t.turno(), t.data(), a.score());
                })
                .toList();
        return new EvidenciaResponse(evidencias, null);
    }

    private static String cortar(String texto) {
        return texto.length() <= ClienteEvidencias.MAXIMO_TEXTO ? texto : texto.substring(0, ClienteEvidencias.MAXIMO_TEXTO);
    }
}
