package com.challengetotvs.api.domain.reuniao;

import com.challengetotvs.api.domain.cliente.Cliente;
import com.challengetotvs.api.domain.cliente.ClienteRepository;
import com.challengetotvs.api.domain.cliente.Contato;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.exception.ApiException;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
@Transactional
public class ReuniaoService {

    private final ClienteRepository clienteRepository;
    private final ReuniaoRepository reuniaoRepository;

    public ReuniaoResponse criar(ReuniaoRequest request, Consultor consultor) {
        var cliente = clienteRepository.findById(request.clienteId())
                .filter(c -> c.getVendedor() != null && c.getVendedor().getId().equals(consultor.getId()))
                .orElseThrow(() -> new EntityNotFoundException("Cliente não encontrado!"));

        var dataHora = request.dataHora().toLocalDateTime();
        validarStatusEData(request.status(), dataHora);

        var contato = escolherContato(cliente, request.contatoId());

        var reuniao = new Reuniao(
                consultor, cliente, contato, dataHora,
                request.titulo().trim(), request.duracaoMin(), request.status()
        );
        reuniaoRepository.save(reuniao);
        return ReuniaoResponse.from(reuniao);
    }

    private void validarStatusEData(StatusReuniao status, LocalDateTime dataHora) {
        if (status == StatusReuniao.ANALISADA) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "status_invalido",
                    "Uma reunião nova só pode ser agendada ou aguardando transcrição.");
        }
        if (status == StatusReuniao.AGENDADA && !dataHora.isAfter(LocalDateTime.now())) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "data_invalida",
                    "Reunião agendada precisa ter data e hora futuras.");
        }
        if (status == StatusReuniao.REALIZADA && dataHora.toLocalDate().isAfter(LocalDate.now())) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "data_invalida",
                    "Reunião já realizada não pode ter data futura.");
        }
    }

    private Contato escolherContato(Cliente cliente, Long contatoId) {
        var contatos = cliente.getContatos();
        if (contatoId == null) {
            return contatos.isEmpty() ? null : contatos.get(0);
        }
        return contatos.stream()
                .filter(c -> c.getId().equals(contatoId))
                .findFirst()
                .orElseThrow(() -> new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "contato_invalido",
                        "O contato não pertence a este cliente."));
    }

    public ReuniaoResponse listarPorId(Long id, Consultor consultor) {
        var reuniao = reuniaoRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Reunião não encontrada!"));

        if (!reuniao.pertenceA(consultor)) {
            throw new AccessDeniedException("Você não tem permissão para acessar essa reunião!");
        }

        return ReuniaoResponse.from(reuniao);
    }

    public Page<ReuniaoResponse> listar(Pageable pagination, Consultor consultor) {
        return reuniaoRepository.findByConsultorWithCliente(consultor, pagination)
                .map(ReuniaoResponse::from);
    }

    public void excluir(Long id, Consultor consultor) {
        var reuniao = reuniaoRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Reunião não foi encontrada!"));

        if (!reuniao.pertenceA(consultor)) {
            throw new AccessDeniedException("Você não tem permissão para acessar essa reunião!");
        }

        reuniaoRepository.deleteById(id);
    }

    public ReuniaoResponse atualizarStatus(Long id, StatusReuniao status, Consultor consultor) {
        var reuniao = reuniaoRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Reunião não foi encontrada!"));

        if (!reuniao.pertenceA(consultor)) {
            throw new AccessDeniedException("Você não tem permissão para acessar essa reunião!");
        }

        reuniao.setStatus(status);
        reuniaoRepository.save(reuniao);
        return ReuniaoResponse.from(reuniao);
    }
}