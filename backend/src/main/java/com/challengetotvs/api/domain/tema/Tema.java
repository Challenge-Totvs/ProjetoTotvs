package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.cliente.Cliente;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Table(name = "TEMA",
        indexes = @Index(name = "IDX_TEMA_CLIENTE_PADRAO", columnList = "cliente_id, padrao_chave"))
@Entity(name = "Tema")
@Getter
@Setter
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Tema {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cliente_id", nullable = false)
    private Cliente cliente;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "padrao_chave", nullable = false)
    private Padrao padrao;

    @Column(nullable = false)
    private String titulo;

    @Column(nullable = false)
    private boolean risco;

    @Column(nullable = false)
    private boolean oportunidade;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "anterior_id")
    private Tema anterior;

    @Column(nullable = false, updatable = false)
    private LocalDateTime criadoEm;

    @Builder
    public Tema(Cliente cliente, Padrao padrao, String titulo,
                boolean risco, boolean oportunidade, Tema anterior) {
        this.cliente = cliente;
        this.padrao = padrao;
        this.titulo = titulo;
        this.risco = risco;
        this.oportunidade = oportunidade;
        this.anterior = anterior;
        this.criadoEm = LocalDateTime.now();
    }
}