package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.transcricao.Transcricao;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Table(name = "ANALISE")
@Entity(name = "Analise")
@Setter
@Getter
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Analise {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "transcricao_id", nullable = false, unique = true)
    private Transcricao transcricao;
    @Lob
    private String pontosInteresse;
    @Lob
    private String pontosDesinteresse;
    @Lob
    private String oportunidadesVenda;
    @Column(nullable = false)
    private int scoreEngajamento;

    @Enumerated(EnumType.STRING)
    private SentimentoGeral sentimentoGeral;
    @Column(nullable = false)
    private LocalDateTime criadoEm;
    @Lob
    private String recomendacaoProximosPassos;
    @Enumerated(EnumType.STRING)
    private MotorUtilizado motorUtilizado;

    @Builder
    public Analise(Transcricao transcricao, String pontosInteresse, String pontosDesinteresse, String oportunidadesVenda, int scoreEngajamento, SentimentoGeral sentimentoGeral, String recomendacaoProximosPassos, MotorUtilizado motorUtilizado){
        this.transcricao = transcricao;
        this.pontosInteresse = pontosInteresse;
        this.pontosDesinteresse = pontosDesinteresse;
        this.oportunidadesVenda = oportunidadesVenda;
        this.scoreEngajamento = scoreEngajamento;
        this.sentimentoGeral = sentimentoGeral;
        this.criadoEm = LocalDateTime.now();
        this.recomendacaoProximosPassos = recomendacaoProximosPassos;
        this.motorUtilizado = motorUtilizado;
    }

    public void atualizar(String pontosInteresse, String pontosDesinteresse, String oportunidadesVenda,
                          int scoreEngajamento, SentimentoGeral sentimentoGeral,
                          String recomendacaoProximosPassos, MotorUtilizado motorUtilizado) {
        this.pontosInteresse = pontosInteresse;
        this.pontosDesinteresse = pontosDesinteresse;
        this.oportunidadesVenda = oportunidadesVenda;
        this.scoreEngajamento = scoreEngajamento;
        this.sentimentoGeral = sentimentoGeral;
        this.recomendacaoProximosPassos = recomendacaoProximosPassos;
        this.motorUtilizado = motorUtilizado;
    }
}
