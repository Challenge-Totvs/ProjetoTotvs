// CitacaoRepository.java
package com.challengetotvs.api.domain.tema;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface CitacaoRepository extends JpaRepository<Citacao, Long> {
    List<Citacao> findByTemaIdOrderByReuniaoDataHoraAsc(Long temaId); // citações do tema, da reunião mais antiga à mais nova (a Calculadora da J7 precisa dessa ordem)
    List<Citacao> findByReuniaoId(Long reuniaoId);                    // "temas citados" da página da reunião
    boolean existsByTemaIdAndReuniaoId(Long temaId, Long reuniaoId);  // já existe citação deste tema nesta reunião?

    /** Citações de todos os temas de um cliente, de uma vez (MontadorTemas.doCliente): evita 1 consulta por tema. */
    List<Citacao> findByTemaClienteIdOrderByReuniaoDataHoraAsc(Long clienteId);
}