package com.challengetotvs.api.domain.reuniao;

import com.challengetotvs.api.domain.cliente.ClienteRepository;
import com.challengetotvs.api.domain.consultor.Consultor;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.data.domain.Page;

import org.springframework.security.access.AccessDeniedException;

@Service
@RequiredArgsConstructor
public class ReuniaoService {

    private final ClienteRepository clienteRepository;
    private final ReuniaoRepository reuniaoRepository;

    public ReuniaoResponse criar(ReuniaoRequest request, Consultor consultor){
       var cliente = clienteRepository.findById(request.clienteId())
               .orElseThrow(() -> new EntityNotFoundException("Cliente não encontrado!"));

       var reuniao = new Reuniao(
               consultor,
               cliente,
               request.dataHora(),
               request.titulo(),
               null
       );

       reuniaoRepository.save(reuniao);
       return ReuniaoResponse.from(reuniao);
    }

    public ReuniaoResponse listarPorId(Long id, Consultor consultor){
        var reuniao = reuniaoRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Reunião não encontrada!"));

        if(!reuniao.getConsultor().getId().equals(consultor.getId())){
            throw new AccessDeniedException("Você não tem permissão para acessar essa reunião!");
        }

        return ReuniaoResponse.from(reuniao);
    }

    public Page<ReuniaoResponse> listar(Pageable pagination, Consultor consultor){
        return reuniaoRepository.findByConsultorWithCliente(consultor, pagination)
                .map(ReuniaoResponse::from);
    }

    public ReuniaoResponse atualizar(ReuniaoRequest request, Consultor consultor, Long id){
        var reuniao = reuniaoRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Reunião não foi encontrada!"));

        if(!reuniao.getConsultor().getId().equals(consultor.getId())){
            throw new AccessDeniedException("Você não tem permissão para acessar essa reunião!");
        }

        var cliente = clienteRepository.findById(request.clienteId())
                .orElseThrow(() -> new EntityNotFoundException("Cliente não encontrado!"));

        reuniao.setCliente(cliente);
        reuniao.setTitulo(request.titulo());
        reuniao.setDataHora(request.dataHora());

        reuniaoRepository.save(reuniao);
        return ReuniaoResponse.from(reuniao);
    }

    public void excluir(Long id, Consultor consultor){
        var reuniao = reuniaoRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Reunião não foi encontrada!"));

        if(!reuniao.getConsultor().getId().equals(consultor.getId())){
            throw new AccessDeniedException("Você não tem permissão para acessar essa reunião!");
        }

        reuniaoRepository.deleteById(id);
    }

    public ReuniaoResponse atualizarStatus(Long id, StatusReuniao status, Consultor consultor){
        var reuniao = reuniaoRepository.findById(id)
                .orElseThrow(() -> new EntityNotFoundException("Reunião não foi encontrada!"));

        if(!reuniao.getConsultor().getId().equals(consultor.getId())){
            throw new AccessDeniedException("Você não tem permissão para acessar essa reunião!");
        }

        reuniao.setStatus(status);
        reuniaoRepository.save(reuniao);
        return ReuniaoResponse.from(reuniao);
    }

}
