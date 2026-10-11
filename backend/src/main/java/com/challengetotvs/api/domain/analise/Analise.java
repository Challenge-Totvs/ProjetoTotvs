package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.transcricao.Transcricao;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Table(name = "ANALISE")
@Entity(name = "Analise")
@Getter
@Setter
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Analise {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "transcricao_id", nullable = false, unique = true)
    private Transcricao transcricao;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private MotorUtilizado motor;

    @Lob
    private String tentativas;

    private Integer score;

    @Enumerated(EnumType.STRING)
    @Column(length = 10)
    private SentimentoGeral sentimento;

    @Lob private String resumo;
    @Lob private String papeis;
    @Lob private String interesse;
    @Lob private String proximosPassos;
    @Lob private String sentimentoSerie;
    @Lob private String descartados;
    @Lob private String entidades;

    private Long duracaoMs;

    @Column(nullable = false)
    private LocalDateTime criadoEm;

    public Analise(Transcricao transcricao) {
        this.transcricao = transcricao;
        this.criadoEm = LocalDateTime.now();
    }
}