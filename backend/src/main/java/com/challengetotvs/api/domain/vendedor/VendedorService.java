package com.challengetotvs.api.domain.vendedor;

import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.consultor.ConsultorRepository;
import com.challengetotvs.api.domain.inicio.InicioResponse;
import com.challengetotvs.api.domain.inicio.InicioService;
import com.challengetotvs.api.exception.ApiException;
import com.challengetotvs.api.security.Perfis;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class VendedorService {

    private final ConsultorRepository consultorRepository;
    private final InicioService inicioService;

    public List<VendedorResumo> listar(Consultor usuario) {
        Perfis.exigirGestor(usuario);
        return consultorRepository.findAll(Sort.by("nome")).stream()
                .filter(c -> !Perfis.ehGestor(c))
                .map(c -> new VendedorResumo(c.getId(), c.getNome(), c.getEmail(),
                        inicioService.montar(c).desempenho()))
                .toList();
    }

    public InicioResponse inicioDe(Long vendedorId, Consultor usuario) {
        Perfis.exigirGestor(usuario);
        var vendedor = consultorRepository.findById(vendedorId)
                .filter(c -> !Perfis.ehGestor(c))
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND,
                        "vendedor_nao_encontrado", "Vendedor não encontrado."));
        return inicioService.montar(vendedor);
    }
}