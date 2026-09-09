package com.challengetotvs.api.domain.reuniao;

import com.challengetotvs.api.domain.consultor.Consultor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ReuniaoRepository extends JpaRepository<Reuniao, Long> {
    Page<Reuniao> findByConsultor(Consultor consultor, Pageable pageable);
}
