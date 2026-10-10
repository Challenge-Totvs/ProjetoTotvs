package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.reuniao.Reuniao;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Table(name = "CITACAO",
        uniqueConstraints = @UniqueConstraint(name = "UK_CITACAO_TEMA_REUNIAO",
                columnNames = {"tema_id", "reuniao_id"}),
        indexes = @Index(name = "IDX_CITACAO_REUNIAO", columnList = "reuniao_id"))
@Entity(name = "Citacao")
@Getter
@Setter
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Citacao {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "tema_id", nullable = false)
    private Tema tema;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "reuniao_id", nullable = false)
    private Reuniao reuniao;

    @Column(nullable = false)
    private int turno;

    private Integer turnoFim;

    private Boolean tratado;

    @Lob
    @Column(nullable = false)
    private String texto;

    @Column(nullable = false, updatable = false)
    private LocalDateTime criadoEm;

    @Builder
    public Citacao(Tema tema, Reuniao reuniao, int turno, Integer turnoFim,
                   Boolean tratado, String texto) {
        this.tema = tema;
        this.reuniao = reuniao;
        this.turno = turno;
        this.turnoFim = turnoFim;
        this.tratado = tratado;
        this.texto = texto;
        this.criadoEm = LocalDateTime.now();
    }
}