package com.challengetotvs.api.domain.transcricao;

import org.springframework.data.jpa.repository.JpaRepository;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Collection;
import java.util.List;
import java.util.Optional;

public interface TranscricaoRepository extends JpaRepository<Transcricao, Long> {

    Optional<Transcricao> findFirstByHashTextoAndReuniaoClienteId(String hashTexto, Long clienteId);

    Optional<Transcricao> findByReuniaoId(Long reuniaoId);

    /** Transcrições de várias reuniões de uma vez (listagens): evita 1 consulta por reunião. */
    List<Transcricao> findByReuniaoIdIn(Collection<Long> reuniaoIds);

    boolean existsByReuniaoId(Long reuniaoId);

    /** As transcrições do cliente, da reunião mais recente para a mais antiga (a página limita quantas). */
    @Query("select t from Transcricao t join fetch t.reuniao r where r.cliente.id = :clienteId order by r.dataHora desc")
    List<Transcricao> maisRecentesDoCliente(@Param("clienteId") Long clienteId, Pageable pagina);
}