package com.challengetotvs.api.domain.transcricao;

import org.springframework.data.jpa.repository.JpaRepository;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface TranscricaoRepository extends JpaRepository<Transcricao, Long> {

    Optional<Transcricao> findFirstByHashTextoAndReuniaoClienteId(String hashTexto, Long clienteId);

    Optional<Transcricao> findByReuniaoId(Long reuniaoId);

    boolean existsByReuniaoId(Long reuniaoId);

    /** As transcrições do cliente, da reunião mais recente para a mais antiga (a página limita quantas). */
    @Query("select t from Transcricao t join fetch t.reuniao r where r.cliente.id = :clienteId order by r.dataHora desc")
    List<Transcricao> maisRecentesDoCliente(@Param("clienteId") Long clienteId, Pageable pagina);
}