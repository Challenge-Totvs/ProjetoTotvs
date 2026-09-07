package com.challengetotvs.api.domain.consultor;

import jakarta.persistence.*;
import lombok.*;

@Table(name = "CONSULTOR")
@Entity(name = "Consultor")
@Getter
@Setter
@NoArgsConstructor
public class Consultor {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false)
    private String nome;
    @Column(unique = true, nullable = false)
    private String email;
    @Column(nullable = false)
    private String senhaHash;
    private String role;

    @Builder
    public Consultor(String nome, String email, String senhaHash, String role){
        this.nome = nome;
        this.email = email;
        this.senhaHash = senhaHash;
        this.role = role;
    }

}
