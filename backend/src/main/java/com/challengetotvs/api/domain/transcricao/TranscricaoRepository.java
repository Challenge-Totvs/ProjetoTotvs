package com.challengetotvs.api.domain.transcricao;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface TranscricaoRepository extends JpaRepository<Transcricao, Long> {

    Optional<Transcricao> findFirstByHashTextoAndReuniaoClienteId(String hashTexto, Long clienteId);

    boolean existsByReuniaoId(Long reuniaoId);
}