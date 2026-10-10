package com.challengetotvs.api.domain.cliente;

import com.challengetotvs.api.domain.consultor.Consultor;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
public class ClienteService {

    private final ClienteRepository repository;

    @Transactional
    public ClienteResponse criar(ClienteRequest request, Consultor vendedor) {
        var cliente = new Cliente(request.nome().trim(), request.tipo(), request.segmento(), vendedor);
        cliente.adicionarContato(request.contato().nome().trim(), request.contato().cargo().trim());
        repository.save(cliente);
        return ClienteResponse.from(cliente);
    }

    @Transactional(readOnly = true) // mantém a sessão aberta para ler vendedor e contatos ao montar a resposta
    public List<ClienteResponse> listar(Consultor usuario) {
        var clientes = ehGestor(usuario)
                ? repository.findByVendedorIsNotNullOrderByNomeAsc()
                : repository.findByVendedorOrderByNomeAsc(usuario);
        return clientes.stream().map(ClienteResponse::from).toList();
    }

    @Transactional(readOnly = true)
    public ClienteResponse buscar(Long id, Consultor usuario) {
        return repository.findById(id)
                .filter(c -> podeVer(c, usuario))
                .map(ClienteResponse::from)
                .orElseThrow(() -> new EntityNotFoundException("Cliente não encontrado"));
    }

    private boolean ehGestor(Consultor usuario) {
        return "GESTOR".equals(usuario.getRole());
    }

    private boolean podeVer(Cliente cliente, Consultor usuario) {
        if (ehGestor(usuario)) return true;
        return cliente.getVendedor() != null && cliente.getVendedor().getId().equals(usuario.getId());
    }
}