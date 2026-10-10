package com.challengetotvs.api.domain.tema;

import jakarta.persistence.*;
import lombok.*;

@Table(name = "PADRAO")
@Entity(name = "Padrao")
@Getter
@NoArgsConstructor
@EqualsAndHashCode(of = "chave")
public class Padrao {

    @Id
    @Column(length = 40)
    private String chave;

    @Column(nullable = false)
    private String nome;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private TipoPadrao tipo;

    @Column(nullable = false)
    private boolean ativo;

    public Padrao(String chave, String nome, TipoPadrao tipo) {
        this.chave = chave;
        this.nome = nome;
        this.tipo = tipo;
        this.ativo = true;
    }
}