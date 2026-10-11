package com.challengetotvs.api.domain.compromisso;

import com.challengetotvs.api.domain.cliente.Cliente;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.reuniao.Reuniao;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Table(name = "COMPROMISSO", indexes = {
                @Index(name = "IDX_COMPROMISSO_CLIENTE", columnList = "cliente_id"),
                @Index(name = "IDX_COMPROMISSO_REUNIAO", columnList = "reuniao_id")})
@Entity(name = "Compromisso")
@Getter
@Setter
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Compromisso {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cliente_id", nullable = false)
    private Cliente cliente;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "reuniao_id", nullable = false)
    private Reuniao reuniao;

    @Column(nullable = false)
    private int turno;

    @Lob
    @Column(nullable = false)
    private String texto;

    @Column(length = 30)
    private String regraPrazo;

    private LocalDate prazo;

    private LocalDateTime cumpridoEm;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cumprido_por_id")
    private Consultor cumpridoPor;

    @Column(nullable = false, updatable = false)
    private LocalDateTime criadoEm;

    @Builder
    public Compromisso(Cliente cliente, Reuniao reuniao, int turno, String texto,
                       String regraPrazo, LocalDate prazo) {
        this.cliente = cliente;
        this.reuniao = reuniao;
        this.turno = turno;
        this.texto = texto;
        this.regraPrazo = regraPrazo;
        this.prazo = prazo;
        this.criadoEm = LocalDateTime.now();
    }

    public boolean cumprido() {
        return cumpridoEm != null;
    }

    public void cumprir(Consultor por, LocalDateTime quando) {
        if (cumpridoEm == null) {
            this.cumpridoEm = quando;
            this.cumpridoPor = por;
        }
    }

    public void reabrir() {
        this.cumpridoEm = null;
        this.cumpridoPor = null;
    }
}