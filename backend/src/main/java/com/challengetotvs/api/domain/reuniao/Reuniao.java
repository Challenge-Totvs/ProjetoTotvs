package com.challengetotvs.api.domain.reuniao;

import com.challengetotvs.api.domain.cliente.Cliente;
import com.challengetotvs.api.domain.cliente.Contato;
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

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "contato_id")
    private Contato contato;

    @Column(nullable = false)
    private LocalDateTime dataHora;
    @Column(nullable = false)
    private String titulo;

    private Integer duracaoMin;   // Integer (e não int) para aceitar nulo: "sem duração informada"

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private StatusReuniao status;

    private Boolean confirmada;

    @Builder
    public Reuniao(Consultor consultor, Cliente cliente, Contato contato, LocalDateTime dataHora,
                   String titulo, Integer duracaoMin, StatusReuniao status) {
        this.consultor = consultor;
        this.cliente = cliente;
        this.contato = contato;
        this.dataHora = dataHora;
        this.titulo = titulo;
        this.duracaoMin = duracaoMin;
        this.status = status != null ? status : StatusReuniao.AGENDADA;
        this.confirmada = false;
    }

    public boolean foiConfirmada() {
        return Boolean.TRUE.equals(confirmada);
    }

    public boolean pertenceA(Consultor consultor) {
        return this.consultor.getId().equals(consultor.getId());
    }
}