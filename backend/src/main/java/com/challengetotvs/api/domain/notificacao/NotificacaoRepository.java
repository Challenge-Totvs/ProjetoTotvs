package com.challengetotvs.api.domain.notificacao;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface NotificacaoRepository extends JpaRepository<Notificacao, Long> {

    List<Notificacao> findTop50ByOrderByCriadoEmDesc();

    long countByLidaEmIsNull();
}