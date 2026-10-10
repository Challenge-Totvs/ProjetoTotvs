package com.challengetotvs.api.domain.tema;

import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;
import java.util.List;

@Component // o Spring cria este objeto e roda o método run() uma vez, quando a aplicação sobe
public class CargaPadroes implements CommandLineRunner {

    private record Def(String chave, String nome, TipoPadrao tipo) {} // mini-classe só para listar os dados

    private static final List<Def> PADROES = List.of(
            new Def("suporte_insatisfacao", "Insatisfação com o suporte", TipoPadrao.RISCO),
            new Def("preco_objecao", "Objeção de preço", TipoPadrao.RISCO),
            new Def("prazo_implantacao", "Prazo de implantação", TipoPadrao.RISCO),
            new Def("concorrente_citado", "Concorrente citado", TipoPadrao.RISCO),
            new Def("cancelamento_citado", "Cancelamento citado", TipoPadrao.RISCO),
            new Def("adocao_resistencia", "Resistência da equipe", TipoPadrao.RISCO),
            new Def("fiscal_problema", "Problema no fechamento fiscal", TipoPadrao.RISCO),
            new Def("orcamento_restrito", "Orçamento restrito", TipoPadrao.RISCO),
            new Def("expansao_unidade", "Expansão para nova unidade", TipoPadrao.OPORTUNIDADE),
            new Def("modulo_adicional", "Módulo adicional", TipoPadrao.OPORTUNIDADE),
            new Def("integracao", "Integração com outro sistema", TipoPadrao.OPORTUNIDADE),
            new Def("renovacao", "Renovação do contrato", TipoPadrao.OPORTUNIDADE),
            new Def("upgrade_licencas", "Ampliação de licenças", TipoPadrao.OPORTUNIDADE),
            new Def("treinamento", "Treinamento da equipe", TipoPadrao.OPORTUNIDADE)
    );

    private final PadraoRepository repository;

    public CargaPadroes(PadraoRepository repository) { // o Spring entrega o repositório pronto
        this.repository = repository;
    }

    @Override
    public void run(String... args) {
        for (Def d : PADROES) {
            if (!repository.existsById(d.chave())) {                          // só insere o que falta: rodar de novo não duplica nem falha
                repository.save(new Padrao(d.chave(), d.nome(), d.tipo()));
            }
        }
    }
}