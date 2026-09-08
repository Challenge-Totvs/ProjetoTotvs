package com.challengetotvs.api.domain.cliente;

import jakarta.persistence.*;
import lombok.*;

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
    @Column(nullable = false)
    private String empresa;
    @Column(nullable = false)
    private String segmento;

    @Builder
    public Cliente(String nome, String empresa, String segmento){
        this.nome = nome;
        this.empresa = empresa;
        this.segmento = segmento;
    }

    public void atualiazarInformacoes(ClienteRequest dados) {
        if(dados.nome() != null){
            this.nome = dados.nome();
        }
        if(dados.empresa() != null){
            this.empresa = dados.empresa();
        }
        if(dados.segmento() != null){
            this.segmento = dados.segmento();
        }

    }
}
