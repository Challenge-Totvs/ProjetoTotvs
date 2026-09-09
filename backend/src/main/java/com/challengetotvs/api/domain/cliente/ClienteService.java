package com.challengetotvs.api.domain.cliente;

import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ClienteService {

    private final ClienteRepository repository;

    public ClienteResponse criar(ClienteRequest request){
        var cliente = new Cliente(
                request.nome(),
                request.empresa(),
                request.segmento()
        );
        repository.save(cliente);
        return ClienteResponse.from(cliente);

    }

    public Page<ClienteResponse> listar(Pageable pagination){
        return repository.findAll(pagination).map(ClienteResponse::from);
    }

    public ClienteResponse listarPorId(Long id){
        return repository.findById(id)
                .map(ClienteResponse::from)
                .orElseThrow(() -> new EntityNotFoundException("Cliente não encontrado!" + id));

    }

    public ClienteResponse atualizar(ClienteRequest request, Long id){
        var cliente = repository.findById(id)
                                .orElseThrow(() -> new EntityNotFoundException("Cliente não encontrado"));

        cliente.setNome(request.nome());
        cliente.setEmpresa(request.empresa());
        cliente.setSegmento(request.segmento());

        repository.save(cliente);
        return ClienteResponse.from(cliente);

    }

    public void excluir(Long id){
        if(!repository.existsById(id)){
            throw new EntityNotFoundException("Cliente não encontrado!" + id);
        }
        repository.deleteById(id);
    }
}
