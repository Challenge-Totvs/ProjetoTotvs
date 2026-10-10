package com.challengetotvs.api.domain.cliente;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Table(name = "CONTATO")
@Entity(name = "Contato")
@Getter
@NoArgsConstructor
public class Contato {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cliente_id", nullable = false)
    private Cliente cliente;

    @Column(nullable = false)
    private String nome;
    @Column(nullable = false)
    private String cargo;

    public Contato(Cliente cliente, String nome, String cargo) {
        this.cliente = cliente;
        this.nome = nome;
        this.cargo = cargo;
    }
}