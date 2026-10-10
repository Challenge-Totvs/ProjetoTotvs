package com.challengetotvs.api.domain.transcricao;

import com.challengetotvs.api.domain.reuniao.Reuniao;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Table(name = "TRANSCRICAO")
@Entity(name = "Transcricao")
@Getter
@Setter
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Transcricao {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "reuniao_id", nullable = false)
    private Reuniao reuniao;
    @Lob
    @Basic(fetch = FetchType.LAZY)
    @Column(nullable = false)
    private String conteudo;
    @Column(nullable = false)
    private String formatoOrigem;
    @Column(nullable = false)
    private LocalDateTime criadoEm;

    @Column(length = 64)
    private String hashTexto;
    private Integer caracteres;
    private Integer turnos;
    private Integer locutores;
    @Builder
    public Transcricao(Reuniao reuniao, String conteudo, String formatoOrigem,
                       String hashTexto, int caracteres, int turnos, int locutores) {
        this.reuniao = reuniao;
        this.conteudo = conteudo;
        this.formatoOrigem = formatoOrigem;
        this.hashTexto = hashTexto;
        this.caracteres = caracteres;
        this.turnos = turnos;
        this.locutores = locutores;
        this.criadoEm = LocalDateTime.now();
    }
}