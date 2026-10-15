package com.challengetotvs.api.domain.analise;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Collection;
import java.util.List;
import java.util.Optional;


public interface AnaliseRepository extends JpaRepository<Analise, Long>{
    Optional<Analise> findByTranscricaoId(Long transcricaoId);

    /** Análises de várias transcrições de uma vez (listagens): evita 1 consulta por transcrição. */
    List<Analise> findByTranscricaoIdIn(Collection<Long> transcricaoIds);
}
