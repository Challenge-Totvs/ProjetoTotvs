"""Tabela AC1..AC10 -> testes (contrato-v3.md §10). O teste garante que cada nome citado existe,
para a tabela não envelhecer quando um teste for renomeado ou apagado."""
import importlib
import os

import pytest

from conftest import RedeBloqueadaEmTeste

ACEITE = {
    "AC1": ["test_p0_mock::test_ac1_aceita_pedidos_v3", "test_p0_mock::test_ac1_recusa_pedido_invalido_com_422_estruturado"],
    "AC2": ["test_p1_schemas::test_ac2_fixtures_validam", "test_p6_contrato::test_enums_do_python_batem_com_os_valores_do_java",
            "test_p6_contrato::test_enums_e_campos_lidos_direto_dos_arquivos_java"],
    "AC3": ["test_p2_llm::test_llm1_responde_e_a_saida_bate_com_a_fixture", "test_p1_schemas::test_saida_llm_schema_e_estrito",
            "test_p2_llm::test_tema_inventado_vai_para_descartados_com_saida_parcial"],
    "AC4": ["test_p3_citacoes::test_acerto_exato", "test_p3_citacoes::test_diferenca_de_espacos_e_aspas_grava_texto_recebido",
            "test_p3_citacoes::test_turno_errado_mas_vizinho_e_corrigido", "test_p3_citacoes::test_trecho_entre_dois_turnos",
            "test_p3_citacoes::test_trecho_inexistente_e_descartado_com_origem_e_padrao",
            "test_p3_citacoes::test_ac4_fixture_llm_confirma_contra_pedido"],
    "AC5": ["test_p6_orquestrador::test_llm1_ok", "test_p6_orquestrador::test_llm1_falha_e_llm2_responde",
            "test_p6_orquestrador::test_duas_llms_fora_responde_o_local", "test_p6_orquestrador::test_tudo_fora_e_503_estruturado_pelo_router",
            "test_p6_orquestrador::test_llm_lenta_estoura_o_timeout_e_o_total_fica_abaixo_de_100_s"],
    "AC6": ["test_p4_regras::test_cada_padrao_e_encontrado_no_turno_certo",
            "test_p4_regras::test_saida_valida_em_analise_response_com_a_fixture_do_contrato",
            "test_p4_regras::test_sem_trechos_analisaveis_levanta_erro_explicito",
            "test_modelo_local_engine::test_turnos_em_branco_levantam_entrada_sem_trechos"],
    "AC7": ["test_p0_mock::test_ac7_app_importa_sem_chaves_e_sem_carregar_joblib", "test_p0_mock::test_ac7_health_no_formato_do_contrato",
            "test_p5_health::test_sem_chaves_e_sem_joblib_responde_200_degradado"],
    "AC8": ["test_p0_mock::test_ac8_mock_devolve_fixture_e_header"],
    # Lado Python do AC9; o teste Java que lê as mesmas fixtures é do Kelwin (PENDENTE).
    "AC9": ["test_p1_schemas::test_ac2_fixtures_validam", "test_p6_contrato::test_fixtures_usam_so_valores_que_o_java_aceita"],
    # pytest verde sem rede e sem chaves; o smoke real (docs/evidencias/smoke-12-10.md) é manual e está PENDENTE.
    "AC10": ["test_rede_bloqueada::test_conexao_externa_e_bloqueada", "test_p6_rastreabilidade::test_ac10_sem_rede_e_sem_chaves"],
}

PENDENTE = {
    "AC9": "teste Java lendo docs/contrato/resposta-v3-*.json em ContratoV3.Resposta (Kelwin)",
    "AC10": "smoke real com as duas chaves em scripts/smoke_llm.py, registrado em docs/evidencias/smoke-12-10.md (João Paulo)",
}


def test_ac10_sem_rede_e_sem_chaves():
    import socket

    assert not [v for v in os.environ if v.startswith("LLM_") and v.endswith(("_API_KEY", "_MODEL"))]
    with pytest.raises(RedeBloqueadaEmTeste):
        socket.create_connection(("203.0.113.1", 443), timeout=1)


@pytest.mark.parametrize("criterio", sorted(ACEITE, key=lambda a: int(a[2:])))
def test_cada_criterio_aponta_para_testes_que_existem(criterio):
    assert ACEITE[criterio], f"{criterio} sem teste"
    for referencia in ACEITE[criterio]:
        modulo, funcao = referencia.split("::")
        assert callable(getattr(importlib.import_module(modulo), funcao, None)), f"{criterio}: {referencia} não existe"


def test_todos_os_dez_criterios_estao_mapeados():
    assert set(ACEITE) == {f"AC{i}" for i in range(1, 11)}
    assert set(PENDENTE) <= set(ACEITE)
