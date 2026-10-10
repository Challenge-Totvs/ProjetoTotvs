package com.challengetotvs.api.domain.cliente;

import com.challengetotvs.api.domain.consultor.Consultor;
import jakarta.persistence.*;
import lombok.*;

import java.util.ArrayList;
import java.util.List;

@Table(name = "CLIENTE")
@Entity(name = "Cliente")
@Getter
@Setter
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Cliente {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String nome;

    @Enumerated(EnumType.STRING)
    private TipoCliente tipo;

    @Column(nullable = false)
    private String segmento;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "vendedor_id")
    private Consultor vendedor;


    @OneToMany(mappedBy = "cliente", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Contato> contatos = new ArrayList<>();

    @Builder
    public Cliente(String nome, TipoCliente tipo, String segmento, Consultor vendedor) {
        this.nome = nome;
        this.tipo = tipo;
        this.segmento = segmento;
        this.vendedor = vendedor;
    }

    public void adicionarContato(String nome, String cargo) {
        contatos.add(new Contato(this, nome, cargo));
    }
}