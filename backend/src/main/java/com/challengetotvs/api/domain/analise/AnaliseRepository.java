package com.challengetotvs.api.domain.analise;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;


public interface AnaliseRepository extends JpaRepository<Analise, Long>{
    Optional<Analise> findByTranscricaoId(Long transcricaoId);
}
