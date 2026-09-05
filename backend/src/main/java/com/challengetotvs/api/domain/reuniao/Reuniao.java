package com.challengetotvs.api.domain.reuniao;

import com.challengetotvs.api.domain.cliente.Cliente;
import com.challengetotvs.api.domain.consultor.Consultor;
import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Table(name = "REUNIAO")
@Entity(name = "Reuniao")
@Setter
@Getter
@NoArgsConstructor
@EqualsAndHashCode(of = "id")
public class Reuniao {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "consultor_id", nullable = false)
    private Consultor consultor;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "cliente_id", nullable = false)
    private Cliente cliente;
    @Column(nullable = false)
    private LocalDateTime dataHora;
    @Column(nullable = false)
    private String titulo;
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private StatusReuniao status;

    @Builder
    public Reuniao(Consultor consultor, Cliente cliente, LocalDateTime dataHora, String titulo, StatusReuniao status){
        this.consultor = consultor;
        this.cliente = cliente;
        this.dataHora = dataHora;
        this.titulo = titulo;
        this.status = status != null ? status : StatusReuniao.AGENDADA;
    }
}
