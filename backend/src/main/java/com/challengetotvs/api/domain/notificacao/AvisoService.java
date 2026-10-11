package com.challengetotvs.api.domain.notificacao;

import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.tema.CitacaoRepository;
import com.challengetotvs.api.domain.tema.Tema;
import com.challengetotvs.api.domain.tema.TemaRepository;
import com.challengetotvs.api.exception.ApiException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class AvisoService {

    private static final int MAX_MENSAGEM = 500;

    private final NotificacaoRepository notificacoes;
    private final TemaRepository temas;
    private final CitacaoRepository citacoes;

    @Transactional
    public NotificacaoResponse.Item avisar(Long temaId, String mensagem, Consultor autor) {
        var tema = temas.findById(temaId)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "tema_nao_encontrado", "Tema não encontrado."));

        var dono = tema.getCliente().getVendedor();
        if (dono == null || !dono.getId().equals(autor.getId())) {
            throw new ApiException(HttpStatus.FORBIDDEN, "sem_permissao", "Só o vendedor do cliente pode avisar a gestão.");
        }

        var texto = mensagem == null ? null : mensagem.trim();
        if (texto != null && texto.isEmpty()) {
            texto = null;
        }
        if (texto != null && texto.length() > MAX_MENSAGEM) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "mensagem_longa",
                    "A mensagem pode ter no máximo " + MAX_MENSAGEM + " caracteres.");
        }

        var salva = notificacoes.save(Notificacao.builder()
                .de(autor)
                .cliente(tema.getCliente())
                .tema(tema)
                .mensagem(texto)
                .build());
        return item(salva);
    }

    @Transactional
    public void desfazer(Long avisoId, Consultor autor) {
        var aviso = notificacoes.findById(avisoId)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "aviso_nao_encontrado", "Aviso não encontrado."));
        if (!aviso.getDe().getId().equals(autor.getId())) {
            throw new ApiException(HttpStatus.FORBIDDEN, "sem_permissao", "Só quem enviou o aviso pode desfazê-lo.");
        }
        if (aviso.lida()) {
            throw new ApiException(HttpStatus.CONFLICT, "aviso_ja_lido", "A gestão já leu este aviso.");
        }
        notificacoes.delete(aviso);
    }

    @Transactional(readOnly = true)
    public NotificacaoResponse listar(Consultor usuario) {
        exigirGestor(usuario);
        List<NotificacaoResponse.Item> itens = new ArrayList<>();
        for (var n : notificacoes.findTop50ByOrderByCriadoEmDesc()) {
            itens.add(item(n));
        }
        return new NotificacaoResponse(notificacoes.countByLidaEmIsNull(), itens);
    }

    @Transactional
    public void marcarLida(Long id, boolean lida, Consultor usuario) {
        exigirGestor(usuario);
        var n = notificacoes.findById(id)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "notificacao_nao_encontrada", "Notificação não encontrada."));
        if (lida && !n.lida()) {
            n.setLidaEm(LocalDateTime.now());
        } else if (!lida) {
            n.setLidaEm(null);
        }
    }

    private void exigirGestor(Consultor usuario) {
        if (!"GESTOR".equals(usuario.getRole())) {
            throw new ApiException(HttpStatus.FORBIDDEN, "sem_permissao", "Só a gestão acessa os pedidos de apoio.");
        }
    }

    private NotificacaoResponse.Item item(Notificacao n) {
        return new NotificacaoResponse.Item(
                n.getId(),
                new NotificacaoResponse.VendedorRef(n.getDe().getId(), n.getDe().getNome()),
                new NotificacaoResponse.ClienteRef(n.getCliente().getId(), n.getCliente().getNome()),
                temaRef(n.getTema()),
                n.getMensagem(),
                n.getCriadoEm(),
                n.lida());
    }

    private NotificacaoResponse.TemaRef temaRef(Tema t) {
        var tipos = new ArrayList<String>();
        if (t.isRisco()) tipos.add("risco");
        if (t.isOportunidade()) tipos.add("oportunidade");

        var cits = citacoes.findByTemaIdOrderByReuniaoDataHoraAsc(t.getId());
        Boolean ultimaTratado = cits.isEmpty() ? null : cits.get(cits.size() - 1).getTratado();
        return new NotificacaoResponse.TemaRef(t.getId(), t.getTitulo(), tipos, ultimaTratado);
    }
}