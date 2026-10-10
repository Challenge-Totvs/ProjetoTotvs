package com.challengetotvs.api.domain.cliente;

import com.challengetotvs.api.domain.consultor.Consultor;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ClienteRepository extends JpaRepository<Cliente, Long> {

    List<Cliente> findByVendedorOrderByNomeAsc(Consultor vendedor);

    List<Cliente> findByVendedorIsNotNullOrderByNomeAsc();
}