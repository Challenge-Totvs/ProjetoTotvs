// TemaRepository.java
package com.challengetotvs.api.domain.tema;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface TemaRepository extends JpaRepository<Tema, Long> {
    List<Tema> findByClienteId(Long clienteId);   // cliente.id: todos os temas do cliente
    List<Tema> findByClienteIdAndPadraoChaveOrderByCriadoEmAsc(Long clienteId, String padraoChave); // candidatos do IncorporadorTemas (J9): mesmo padrão no cliente, do mais antigo ao mais novo
}