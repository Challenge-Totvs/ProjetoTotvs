"""P8 — leitura de CSV do corpus: bytes inválidos em UTF-8 não derrubam o pipeline (SINTÉTICO)."""
from treino import comum


def test_csv_com_byte_invalido_le_sem_erro_e_conta_linhas(tmp_path):
    caminho = tmp_path / "corpus.csv"
    caminho.write_bytes("id,texto\r\n1,ação válida\r\n2,fim ".encode("utf-8") + b"\xaa" + b" da linha\r\n")
    assert comum.cabecalho_csv(caminho) == (["id", "texto"], 2)
    linhas = comum.ler_csv(caminho)
    assert linhas[0]["texto"] == "ação válida" and "�" in linhas[1]["texto"] and len(linhas) == 2


# ------------------------------------------------------------------ corpus no formato quebrado (SINTÉTICO)

CABECALHO = ("ID_MEETING,DT_MEETING,FORMATO_MEETING,ID_STATUS_MEETING,STATUS_MEETING,DURACAO_MEETING,CODT,"
             "TP_RECURSO,FLG_EXTERNO,DT_CRIACAO,ANON_TRANSCRICAO,UF,CNAE,NOME_UNIDADE,NOME_SEGMENTO,"
             "FAIXA_FATURAMENTO_CLIENTE_EC,DT_ULTIMA_PESQUISA,NOTA_NPS")


def registro_quebrado(id_: int, turnos: list[str]) -> list[str]:
    """Só a 1ª e a última linha física vêm entre aspas (com `\"` dobradas); as do meio vêm soltas."""
    inicio = f'{id_},2026-03-18 16:00:00,VIDEO,3,COMPLETED,01:39:13,T{id_ % 7},,true,2026-03-13 16:47:22,"{turnos[0]}'
    fim = f'{turnos[-1]}",DF,8610-1/02,UNIDADE X,SAUDE,06.SMB III - De R$ 1 a R$ 2,,'
    if len(turnos) == 1:
        return ['"' + (inicio + '",DF,8610-1/02,UNIDADE X,SAUDE,06.SMB III - De R$ 1 a R$ 2,,').replace('"', '""') + '"']
    return ['"' + inicio.replace('"', '""') + '"', *turnos[1:-1], '"' + fim.replace('"', '""') + '"']


def corpus_quebrado(tmp_path):
    linhas = [CABECALHO]
    linhas += registro_quebrado(11, ["[LOCUTOR 1]: Olá, tudo bem?", "[LOCUTOR 2]: Tudo, e você, [PESSOA]?",
                                     '[LOCUTOR 1]: Ele disse "ok", certo.', "[LOCUTOR 2]: Fechado."])
    linhas += registro_quebrado(12, ["[LOCUTOR 1]: Turno único, com vírgula."])
    linhas += registro_quebrado(13, ["[LOCUTOR 1]: Primeiro.", "[LOCUTOR 2]: Último, com vírgula."])
    caminho = tmp_path / "corpus.csv"
    caminho.write_bytes(("\r\n".join(linhas) + "\r\n").encode("utf-8"))
    return caminho


def test_corpus_quebrado_e_reconstruido_por_reuniao(tmp_path):
    reunioes = comum.ler_corpus(corpus_quebrado(tmp_path))
    assert [r["ID_MEETING"] for r in reunioes] == ["11", "12", "13"]
    assert len(reunioes[0]) == 18 and reunioes[0]["CODT"] == "T4" and reunioes[0]["UF"] == "DF"
    assert reunioes[0]["ANON_TRANSCRICAO"] == ('[LOCUTOR 1]: Olá, tudo bem?\n[LOCUTOR 2]: Tudo, e você, [PESSOA]?\n'
                                               '[LOCUTOR 1]: Ele disse "ok", certo.\n[LOCUTOR 2]: Fechado.')
    assert reunioes[1]["ANON_TRANSCRICAO"] == "[LOCUTOR 1]: Turno único, com vírgula."
    assert reunioes[2]["ANON_TRANSCRICAO"] == "[LOCUTOR 1]: Primeiro.\n[LOCUTOR 2]: Último, com vírgula."
    assert reunioes[2]["FAIXA_FATURAMENTO_CLIENTE_EC"] == "06.SMB III - De R$ 1 a R$ 2"
    assert comum.cabecalho_corpus(corpus_quebrado(tmp_path)) == (CABECALHO.split(","), 3)


def test_corpus_normal_continua_lido_pelo_csv_padrao(tmp_path):
    caminho = tmp_path / "ok.csv"
    comum.gravar_csv(caminho, [{"ID_MEETING": "1", "CODT": "T1", "ANON_TRANSCRICAO": "[LOCUTOR 1]: a\n[LOCUTOR 2]: b"}],
                     ["ID_MEETING", "CODT", "ANON_TRANSCRICAO"])
    assert comum.ler_corpus(caminho)[0]["ANON_TRANSCRICAO"] == "[LOCUTOR 1]: a\n[LOCUTOR 2]: b"
    assert comum.cabecalho_corpus(caminho) == (["ID_MEETING", "CODT", "ANON_TRANSCRICAO"], 1)


def test_corpus_quebrado_registro_que_nao_fecha_e_so_contado(tmp_path):
    caminho = corpus_quebrado(tmp_path)
    linhas = caminho.read_bytes().decode("utf-8").split("\r\n")
    linhas.insert(len(linhas) - 1, registro_quebrado(14, ["[LOCUTOR 1]: x", "[LOCUTOR 2]: y"])[0])  # só o início
    caminho.write_bytes("\r\n".join(linhas).encode("utf-8"))
    contagem: dict = {}
    reunioes = comum.ler_corpus(caminho, contagem)
    assert [r["ID_MEETING"] for r in reunioes] == ["11", "12", "13"] and contagem["registros_invalidos"] == 1


def test_extrair_trechos_aceita_corpus_quebrado(tmp_path, capsys):
    from treino import extrair_trechos

    comum.gravar_csv(tmp_path / "holdout.csv", [{"ID_MEETING": "99", "CODT": "T5", "no_ouro": "1"}],
                     ["ID_MEETING", "CODT", "no_ouro"])
    assert extrair_trechos.main(["--corpus", str(corpus_quebrado(tmp_path)), "--holdout", str(tmp_path / "holdout.csv"),
                                 "--saida", str(tmp_path / "trechos.csv"), "--col-reuniao", "ID_MEETING",
                                 "--col-cliente", "CODT", "--col-texto", "ANON_TRANSCRICAO"]) == 0
    resumo = capsys.readouterr().out
    assert '"reunioes_usadas": 2' in resumo and '"reunioes_excluidas_holdout": 1' in resumo
