// EventoTemaRepository.java
package com.challengetotvs.api.domain.tema;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.Optional;

public interface EventoTemaRepository extends JpaRepository<EventoTema, Long> {
    List<EventoTema> findByTemaIdOrderByCriadoEmAsc(Long temaId);     // histórico completo do tema
    Optional<EventoTema> findFirstByTemaIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(Long temaId, TipoEvento tipo); // o vigente de cada tipo: o mais recente sem desfeitoEm
}