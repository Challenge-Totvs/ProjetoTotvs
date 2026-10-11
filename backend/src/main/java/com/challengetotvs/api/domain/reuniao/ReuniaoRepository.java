package com.challengetotvs.api.domain.reuniao;

import com.challengetotvs.api.domain.consultor.Consultor;
import org.hibernate.annotations.Parent;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface ReuniaoRepository extends JpaRepository<Reuniao, Long> {
    @Query(value = "SELECT r FROM Reuniao r JOIN FETCH r.cliente WHERE r.consultor = :consultor")
    Page<Reuniao> findByConsultorWithCliente(@Param("consultor") Consultor consultor, Pageable pageable);

    List<Reuniao> findByClienteIdOrderByDataHoraDesc(Long clienteId);
}
