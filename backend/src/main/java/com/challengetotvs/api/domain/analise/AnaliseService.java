package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.analise.Pseudonimizador.Entidade;
import com.challengetotvs.api.domain.analise.Pseudonimizador.Tipo;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.tema.Padrao;
import com.challengetotvs.api.domain.tema.PadraoRepository;
import com.challengetotvs.api.domain.transcricao.LeitorTurnos;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import com.challengetotvs.api.exception.AnaliseIndisponivelException;
import com.challengetotvs.api.exception.ApiException;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class AnaliseService {     // SEM @Transactional: a espera pelo Python não pode segurar o banco

    private final TranscricaoRepository transcricaoRepository;
    private final PadraoRepository padraoRepository;
    private final AnaliseStrategy strategy;
    private final GravadorAnalise gravador;

    public AnalisarResponse analisar(Long transcricaoId, Consultor consultor) {
        var transcricao = transcricaoRepository.findById(transcricaoId)
                .filter(t -> t.getReuniao().pertenceA(consultor))
                .orElseThrow(() -> new EntityNotFoundException("Transcrição não encontrada!"));
        Reuniao reuniao = transcricao.getReuniao();

        var pseudonimizador = new Pseudonimizador(entidadesDoCadastro(reuniao));

        var turnos = LeitorTurnos.ler(transcricao.getConteudo()).stream()
                .map(t -> new ContratoV3.TurnoPedido(t.n(), t.locutor(), pseudonimizador.pseudonimizar(t.texto())))
                .toList();
        if (turnos.isEmpty()) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "sem_locutor",
                    "Não encontrei marcações [LOCUTOR n] na transcrição.");
        }

        var padroes = padraoRepository.findByAtivoTrueOrderByNomeAsc().stream().map(Padrao::getChave).toList();
        var pedido = new ContratoV3.Pedido(turnos, reuniao.getDataHora().toLocalDate().toString(), padroes, List.of());

        long inicio = System.nanoTime();
        var resposta = strategy.analisar(pedido);
        long duracaoMs = (System.nanoTime() - inicio) / 1_000_000;
        if (resposta == null) {
            throw new AnaliseIndisponivelException("O serviço de análise devolveu uma resposta vazia.");
        }

        var analise = gravador.gravar(transcricao, resposta, pseudonimizador, duracaoMs);

        return new AnalisarResponse(reuniao.getId(), analise.getMotor().valor(), resposta.tentativas(), 0, 0, 0);
    }

    private List<Entidade> entidadesDoCadastro(Reuniao reuniao) {
        var lista = new ArrayList<Entidade>();
        var cliente = reuniao.getCliente();
        lista.add(new Entidade(cliente.getNome(), Tipo.EMPRESA));
        cliente.getContatos().forEach(c -> adicionarPessoa(lista, c.getNome()));
        adicionarPessoa(lista, reuniao.getConsultor().getNome());
        return lista;
    }

    private void adicionarPessoa(List<Entidade> lista, String nome) {
        if (nome == null || nome.isBlank()) {
            return;
        }
        String completo = nome.strip();
        lista.add(new Entidade(completo, Tipo.PESSOA));
        String primeiro = completo.split("\\s+")[0];
        if (!primeiro.equals(completo) && primeiro.length() >= 3) {   // nome de uma palavra só não duplica; "Zé" curto demais é ignorado
            lista.add(new Entidade(primeiro, Tipo.PESSOA));
        }
    }
}