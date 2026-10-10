// PadraoRepository.java
package com.challengetotvs.api.domain.tema;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface PadraoRepository extends JpaRepository<Padrao, String> { // o 2º tipo é o da chave: String, não Long
    List<Padrao> findByAtivoTrueOrderByNomeAsc();                          // o Spring monta a query só pelo nome do método: ativos, por nome
}