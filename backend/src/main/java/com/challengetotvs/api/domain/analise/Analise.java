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

    private String sentimentoGeral;
    @Column(nullable = false)
    private LocalDateTime criadoEm;

    @Builder
    public Analise(Transcricao transcricao, String pontosInteresse, String pontosDesinteresse, String oportunidadesVenda, int scoreEngajamento, String sentimentoGeral){
        this.transcricao = transcricao;
        this.pontosInteresse = pontosInteresse;
        this.pontosDesinteresse = pontosDesinteresse;
        this.oportunidadesVenda = oportunidadesVenda;
        this.scoreEngajamento = scoreEngajamento;
        this.sentimentoGeral = sentimentoGeral;
        this.criadoEm = LocalDateTime.now();
    }
}
