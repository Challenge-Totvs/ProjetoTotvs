package com.challengetotvs.api.domain.inicio.semanal;

import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.Repository;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.Collection;
import java.util.List;

/**
 * Consulta só de leitura para a série semanal do Início. Separado de {@code ReuniaoRepository}
 * de propósito: não compartilha métodos com o hot-path de {@code InicioService.montar}.
 */
public interface InicioSemanalRepository extends Repository<Reuniao, Long> {

    @Query("""
            SELECT r.dataHora AS dataHora, r.status AS status, a.score AS score
            FROM Reuniao r
            LEFT JOIN Transcricao t ON t.reuniao = r
            LEFT JOIN Analise a ON a.transcricao = t
            WHERE r.consultor.id = :consultorId
              AND r.status IN :statuses
              AND r.dataHora >= :desde
            """)
    List<ReuniaoSemanalRow> buscarDesde(@Param("consultorId") Long consultorId,
                                         @Param("statuses") Collection<StatusReuniao> statuses,
                                         @Param("desde") LocalDateTime desde);

    interface ReuniaoSemanalRow {
        LocalDateTime getDataHora();
        StatusReuniao getStatus();
        Integer getScore();
    }
}
