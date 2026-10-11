package com.challengetotvs.api.domain.notificacao;

import com.challengetotvs.api.domain.cliente.Cliente;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.tema.Tema;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;

@Table(name = "NOTIFICACAO", indexes = @Index(name = "IDX_NOTIFICACAO_CRIADO", columnList = "criadoEm"))
@Entity(name = "Notificacao")
@Getter
@Setter
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Notificacao {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "de_id", nullable = false)
    private Consultor de;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cliente_id", nullable = false)
    private Cliente cliente;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "tema_id", nullable = false)
    private Tema tema;

    @Column(length = 500)
    private String mensagem;

    @Column(nullable = false, updatable = false)
    private LocalDateTime criadoEm;

    private LocalDateTime lidaEm;

    @Builder
    public Notificacao(Consultor de, Cliente cliente, Tema tema, String mensagem) {
        this.de = de;
        this.cliente = cliente;
        this.tema = tema;
        this.mensagem = mensagem;
        this.criadoEm = LocalDateTime.now();
    }

    public boolean lida() {
        return lidaEm != null;
    }
}