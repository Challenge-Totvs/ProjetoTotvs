from app.engines import modelo_local_engine
from app.schemas import MotorUtilizado
import pytest

transcricao_b = """[00:03] Consultor: Bom dia, João. Como está o uso do sistema?
[00:12] Cliente: Bom dia. Olha, sendo bem sincero, não estamos satisfeitos.
[00:20] Cliente: O suporte demora demais pra responder, já abrimos 3 chamados esse mês.
[01:10] Cliente: Estamos avaliando seriamente cancelar e migrar pra outro fornecedor.
"""

def test_analisar_com_objecao_classifica_como_motor_local():
    resultado = modelo_local_engine.analisar(transcricao_b)
    assert resultado.motorUtilizado == MotorUtilizado.MODELO_LOCAL
    assert 0 <= resultado.scoreEngajamento <= 100

def test_analisar_transcricao_vazia_lanca_erro():
    with pytest.raises(ValueError):
        modelo_local_engine.analisar("")