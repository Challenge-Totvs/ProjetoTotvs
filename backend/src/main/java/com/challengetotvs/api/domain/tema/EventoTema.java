package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.consultor.Consultor;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Table(name = "EVENTO_TEMA",
        indexes = @Index(name = "IDX_EVENTO_TEMA_TEMA", columnList = "tema_id"))
@Entity(name = "EventoTema")
@Getter
@Setter
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class EventoTema {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "tema_id", nullable = false)
    private Tema tema;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private TipoEvento tipo;

    private String acao;
    private String canal;
    private LocalDate dataAcao;
    @Column(length = 500)
    private String observacao;
    private String motivo;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "por_id", nullable = false)
    private Consultor por;

    @Column(nullable = false, updatable = false)
    private LocalDateTime criadoEm;

    private LocalDateTime desfeitoEm;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "desfeito_por_id")
    private Consultor desfeitoPor;

    @Builder
    public EventoTema(Tema tema, TipoEvento tipo, String acao, String canal,
                      LocalDate dataAcao, String observacao, String motivo, Consultor por) {
        this.tema = tema;
        this.tipo = tipo;
        this.acao = acao;
        this.canal = canal;
        this.dataAcao = dataAcao;
        this.observacao = observacao;
        this.motivo = motivo;
        this.por = por;
        this.criadoEm = LocalDateTime.now();
    }

    public boolean vigente() {
        return desfeitoEm == null;       // vigente = ainda não foi desfeito
    }

    public void desfazer(Consultor quem) {
        if (!vigente()) return;
        this.desfeitoEm = LocalDateTime.now();
        this.desfeitoPor = quem;
    }
}