package com.challengetotvs.api.domain.compromisso;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CompromissoRepository extends JpaRepository<Compromisso, Long> {

    List<Compromisso> findByClienteVendedorId(Long vendedorId);

    List<Compromisso> findByClienteId(Long clienteId);

    List<Compromisso> findByReuniaoId(Long reuniaoId);

    void deleteByReuniaoId(Long reuniaoId);
}