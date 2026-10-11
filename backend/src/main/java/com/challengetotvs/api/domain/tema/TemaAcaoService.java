package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.exception.ApiException;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.Optional;

@Service
@RequiredArgsConstructor
@Transactional
public class TemaAcaoService {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");

    private final TemaRepository temaRepository;
    private final CitacaoRepository citacaoRepository;
    private final EventoTemaRepository eventoTemaRepository;
    private final MontadorTemas montadorTemas;


    public TemaResponse registrarForaDaReuniao(Long temaId, TratadoForaRequest request, Consultor usuario) {
        Tema tema = buscarDoVendedor(temaId, usuario);

        if (vigente(temaId, TipoEvento.NAO_PROCEDE).isPresent()) {
            throw new ApiException(HttpStatus.CONFLICT, "tema_nao_procede",
                    "Um tema marcado como não procede não aceita registro fora da reunião.");
        }
        if (vigente(temaId, TipoEvento.TRATADO_FORA).isPresent()) {
            throw new ApiException(HttpStatus.CONFLICT, "registro_ja_existe",
                    "Este tema já tem um registro fora da reunião. Remova o atual antes de registrar outro.");
        }

        if (!RegrasAcaoTema.acaoValida(request.acao(), tema.isRisco(), tema.isOportunidade())) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "acao_invalida_para_o_tipo",
                    "Escolha o que foi feito.");
        }
        String canal = (request.canal() == null || request.canal().isBlank())
                ? RegrasAcaoTema.CANAL_PADRAO : request.canal();
        if (!RegrasAcaoTema.canalValido(canal)) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "canal_invalido", "Canal inválido.");
        }

        LocalDate hoje = LocalDate.now(FUSO);
        LocalDate data = request.data() == null ? hoje : request.data();
        if (RegrasAcaoTema.dataFutura(data, hoje)) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "data_futura",
                    "A data não pode ser no futuro.");
        }

        var citacoes = citacaoRepository.findByTemaIdOrderByReuniaoDataHoraAsc(temaId);
        if (citacoes.isEmpty()) {
            throw new EntityNotFoundException("Tema sem citações!");
        }
        LocalDate ultima = citacoes.get(citacoes.size() - 1).getReuniao().getDataHora().toLocalDate();
        if (RegrasAcaoTema.anteriorAUltimaCitacao(data, ultima)) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "data_anterior_a_citacao",
                    "A data não pode ser anterior à última reunião em que o tema apareceu.");
        }

        String observacao = (request.observacao() == null || request.observacao().isBlank())
                ? null : request.observacao().strip();
        eventoTemaRepository.save(EventoTema.builder()
                .tema(tema)
                .tipo(TipoEvento.TRATADO_FORA)
                .acao(request.acao())
                .canal(canal)
                .dataAcao(data)
                .observacao(observacao)
                .por(usuario)
                .build());

        return montadorTemas.doTema(temaId, true);
    }

    public TemaResponse removerForaDaReuniao(Long temaId, Consultor usuario) {
        buscarDoVendedor(temaId, usuario);
        desfazer(temaId, TipoEvento.TRATADO_FORA, usuario);
        return montadorTemas.doTema(temaId, true);
    }


    public TemaResponse marcarNaoProcede(Long temaId, String motivo, Consultor usuario) {
        Tema tema = buscarDoVendedor(temaId, usuario);

        if (!RegrasAcaoTema.motivoValido(motivo)) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "motivo_invalido", "Motivo inválido.");
        }
        if (vigente(temaId, TipoEvento.NAO_PROCEDE).isPresent()) {
            throw new ApiException(HttpStatus.CONFLICT, "ja_nao_procede", "Este tema já está marcado como não procede.");
        }

        eventoTemaRepository.save(EventoTema.builder()
                .tema(tema)
                .tipo(TipoEvento.NAO_PROCEDE)
                .motivo(motivo == null || motivo.isBlank() ? null : motivo)
                .por(usuario)
                .build());

        return montadorTemas.doTema(temaId, true);
    }

    public TemaResponse desfazerNaoProcede(Long temaId, Consultor usuario) {
        buscarDoVendedor(temaId, usuario);
        desfazer(temaId, TipoEvento.NAO_PROCEDE, usuario);
        return montadorTemas.doTema(temaId, true);
    }


    private Tema buscarDoVendedor(Long temaId, Consultor usuario) {
        return temaRepository.findById(temaId)
                .filter(t -> t.getCliente().getVendedor() != null
                        && t.getCliente().getVendedor().getId().equals(usuario.getId()))
                .orElseThrow(() -> new EntityNotFoundException("Tema não encontrado!"));
    }

    private Optional<EventoTema> vigente(Long temaId, TipoEvento tipo) {
        return eventoTemaRepository.findFirstByTemaIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(temaId, tipo);
    }

    private void desfazer(Long temaId, TipoEvento tipo, Consultor usuario) {
        EventoTema evento = vigente(temaId, tipo)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "sem_registro",
                        "Não há registro vigente para remover."));
        evento.desfazer(usuario);
        eventoTemaRepository.save(evento);
    }
}