package com.challengetotvs.api.domain.consultor;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface ConsultorRepository extends JpaRepository<Consultor, Long> {
    Optional<Consultor> findByEmail(String email);
}