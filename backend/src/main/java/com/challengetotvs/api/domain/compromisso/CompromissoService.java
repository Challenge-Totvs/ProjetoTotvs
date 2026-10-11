package com.challengetotvs.api.domain.compromisso;

import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.exception.ApiException;
import com.challengetotvs.api.security.Perfis;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CompromissoService {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");
    private static final int DIAS_CUMPRIDO_NO_INICIO = 3;

    private final CompromissoRepository repository;

    public record ResumoInicio(List<CompromissoResponse> lista, int vencidos) {
    }

    public ResumoInicio doInicio(Long vendedorId, LocalDate hoje) {
        var todos = repository.findByClienteVendedorId(vendedorId).stream()
                .map(c -> CompromissoResponse.de(c, hoje))
                .toList();
        int vencidos = (int) todos.stream().filter(c -> "vencido".equals(c.estado())).count();
        var lista = todos.stream()
                .filter(c -> !c.cumprido()
                        || ChronoUnit.DAYS.between(c.cumpridoEm(), hoje) <= DIAS_CUMPRIDO_NO_INICIO)
                .sorted(CompromissoResponse.ORDEM)
                .toList();
        return new ResumoInicio(lista, vencidos);
    }

    public List<CompromissoResponse> doCliente(Long clienteId) {
        return ordenados(repository.findByClienteId(clienteId));
    }

    public List<CompromissoResponse> daReuniao(Long reuniaoId) {
        return ordenados(repository.findByReuniaoId(reuniaoId));
    }

    public List<CompromissoResponse> listar(Long vendedorId, Long clienteId, Long reuniaoId, Consultor usuario) {
        List<Compromisso> base;
        if (reuniaoId != null) {
            base = repository.findByReuniaoId(reuniaoId);
        } else if (clienteId != null) {
            base = repository.findByClienteId(clienteId);
        } else if (!Perfis.ehGestor(usuario)) {
            base = repository.findByClienteVendedorId(usuario.getId());
        } else if (vendedorId != null) {
            base = repository.findByClienteVendedorId(vendedorId);
        } else {
            base = repository.findAll();
        }
        if (!Perfis.ehGestor(usuario)) {
            base = base.stream().filter(c -> ehDono(c, usuario)).toList();
        }
        return ordenados(base);
    }

    @Transactional
    public CompromissoResponse marcar(Long id, boolean cumprido, Consultor usuario) {
        var c = repository.findById(id)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND,
                        "compromisso_nao_encontrado", "Compromisso não encontrado."));
        if (!ehDono(c, usuario)) {
            throw new ApiException(HttpStatus.FORBIDDEN, "sem_permissao",
                    "Só o vendedor do cliente pode marcar o compromisso.");
        }
        if (cumprido) {
            c.cumprir(usuario, LocalDateTime.now(FUSO));
        } else {
            c.reabrir();
        }
        return CompromissoResponse.de(c, LocalDate.now(FUSO));
    }

    private boolean ehDono(Compromisso c, Consultor usuario) {
        var dono = c.getCliente().getVendedor();
        return dono != null && dono.getId().equals(usuario.getId());
    }

    private List<CompromissoResponse> ordenados(List<Compromisso> compromissos) {
        var hoje = LocalDate.now(FUSO);
        return compromissos.stream()
                .map(c -> CompromissoResponse.de(c, hoje))
                .sorted(CompromissoResponse.ORDEM)
                .toList();
    }
}