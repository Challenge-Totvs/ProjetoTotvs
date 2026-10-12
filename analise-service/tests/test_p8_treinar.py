"""P8 etapa 4 — treinar.py: clone do Pipeline base (D17), dados SINTÉTICOS, nada em app/modelos."""
import json
import subprocess
import sys
from pathlib import Path

import joblib
import pytest

from sintetico_p8 import STOP_WORDS_SINTETICAS, base_sintetica, rotulos_sinteticos
from treino import comum, treinar

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def cenario(tmp_path):
    return {"base": base_sintetica(tmp_path / "base.joblib"), "rotulos": rotulos_sinteticos(tmp_path),
            "candidatos": tmp_path / "candidatos", "pasta": tmp_path}


def _args(c, *extra):
    return ["--rotulos", str(c["rotulos"]), "--base", str(c["base"]), "--candidatos", str(c["candidatos"]),
            "--holdout", str(c["pasta"] / "nao-existe.csv"), "--ouro", str(c["pasta"] / "nao-existe-ouro.csv"),
            "--veredito", str(c["pasta"] / "nao-existe-veredito.json"), *extra]


def test_treina_os_dois_candidatos_com_os_hiperparametros_da_base(cenario, capsys):
    assert treinar.main(_args(cenario)) == 0
    pasta = next(cenario["candidatos"].iterdir())
    base = joblib.load(cenario["base"])
    for nome in ("risco", "interesse"):
        modelo = joblib.load(pasta / f"{nome}.joblib")
        assert [n for n, _ in modelo.steps] == [n for n, _ in base.steps]
        for chave, valor in base.get_params(deep=True).items():
            if "__" in chave:
                assert modelo.get_params(deep=True)[chave] == valor, chave
        assert modelo.named_steps["tfidf"].stop_words == STOP_WORDS_SINTETICAS  # herdada, não uma lista nova
        assert modelo.predict_proba(["O suporte demora demais."]).shape == (1, 2)
    meta = json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))
    assert meta["mudancas"] == [] and meta["dados"]["sha256"] == comum.sha256_arquivo(cenario["rotulos"])
    assert meta["scikit_learn"] == __import__("sklearn").__version__
    assert meta["hiperparametros"]["tfidf__stop_words"] == f"<list len={len(STOP_WORDS_SINTETICAS)}>"
    assert meta["tamanhos"]["risco"]["positivos"] > 0 and meta["tamanhos"]["interesse"]["positivos"] > 0
    impresso = capsys.readouterr().out
    assert all(x["texto"] not in impresso for x in comum.ler_csv(cenario["rotulos"]))


def test_o_clone_nao_altera_a_base(cenario):
    antes = comum.sha256_arquivo(cenario["base"])
    treinar.main(_args(cenario))
    assert comum.sha256_arquivo(cenario["base"]) == antes


def test_mudar_hiperparametro_exige_justificativa_e_fica_registrado(cenario):
    with pytest.raises(SystemExit):
        treinar.main(_args(cenario, "--param", "clf__C=0.5"))
    assert treinar.main(_args(cenario, "--param", "clf__C=0.5", "--justificativa", "teste sintético")) == 0
    pasta = next(cenario["candidatos"].iterdir())
    meta = json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))
    assert meta["mudancas"] == [{"parametro": "clf__C", "valor": 0.5, "valor_base": 1.0, "justificativa": "teste sintético"}]
    assert joblib.load(pasta / "risco.joblib").named_steps["clf"].C == 0.5


def test_reuniao_do_holdout_no_treino_aborta(cenario):
    reuniao = comum.ler_csv(cenario["rotulos"])[0]["reuniao"]
    holdout = cenario["pasta"] / "holdout.csv"
    comum.gravar_csv(holdout, [{"reuniao": reuniao}], ["reuniao"])
    args = _args(cenario)
    args[args.index("--holdout") + 1] = str(holdout)
    with pytest.raises(SystemExit, match="holdout"):
        treinar.main(args)
    assert not cenario["candidatos"].exists()


def test_id_do_ouro_no_treino_aborta(cenario):
    primeiro = comum.ler_csv(cenario["rotulos"])[0]
    ouro = cenario["pasta"] / "ouro.csv"
    comum.gravar_csv(ouro, [{"id": primeiro["id"], "texto": primeiro["texto"]}], ["id", "texto"])
    args = _args(cenario)
    args[args.index("--ouro") + 1] = str(ouro)
    with pytest.raises(SystemExit, match="ouro"):
        treinar.main(args)


def test_uma_classe_so_para_com_mensagem(cenario):
    linhas = comum.ler_csv(cenario["rotulos"])
    for x in linhas:
        x["interesse"] = "0"
    comum.gravar_csv(cenario["rotulos"], linhas, list(linhas[0]))
    with pytest.raises(SystemExit, match="uma classe"):
        treinar.main(_args(cenario))


def test_nao_sobrescreve_candidato_do_mesmo_dia(cenario):
    treinar.main(_args(cenario))
    treinar.main(_args(cenario))
    assert len(list(cenario["candidatos"].iterdir())) == 2


def test_padrao_e_o_artefato_do_repo_e_a_saida_em_dados_locais():
    assert treinar.CAMINHO_MODELO_ATUAL == RAIZ / "app" / "modelos" / "classificador_risco.joblib"
    assert comum.DADOS == RAIZ / "dados_locais"


def test_clone_do_artefato_real_herda_os_hiperparametros_d17():
    base = treinar.carregar_base(treinar.CAMINHO_MODELO_ATUAL)
    novo = treinar.novo_modelo(base, {})
    params = treinar.hiperparametros(novo)
    assert params["tfidf__ngram_range"] == [1, 2] and params["tfidf__min_df"] == 5 and params["tfidf__max_df"] == 0.6
    assert params["tfidf__stop_words"] == "<list len=315>" and params["clf__class_weight"] == "balanced"
    assert not hasattr(novo.named_steps["clf"], "coef_")  # nada aprendido vem junto


def test_help_roda():
    r = subprocess.run([sys.executable, "treino/treinar.py", "--help"], cwd=RAIZ, capture_output=True)
    assert r.returncode == 0 and b"--justificativa" in r.stdout


def _metadatas(cenario) -> list[dict]:
    return [json.loads((p / "metadata.json").read_text(encoding="utf-8")) for p in sorted(cenario["candidatos"].iterdir())]


def _com_veredito(cenario, conteudo: str) -> list[str]:
    caminho = cenario["pasta"] / "professora_veredito.json"
    caminho.write_text(conteudo, encoding="utf-8")
    args = _args(cenario)
    args[args.index("--veredito") + 1] = str(caminho)
    return args


def test_sem_veredito_da_professora_registra_sem_veredito(cenario):
    assert treinar.main(_args(cenario)) == 0
    n = len(comum.ler_csv(cenario["rotulos"]))
    assert _metadatas(cenario)[0]["professora"] == {
        "arquivo": None, "data": None, "avisos": [],
        "grupos": {g: {"veredito": "sem_veredito", "rotulos_llm": 0, "rotulos_regra": n} for g in ("risco", "interesse")}}


def test_veredito_da_professora_e_registrado_por_grupo_sem_mudar_o_rotulo(cenario, capsys):
    linhas = comum.ler_csv(cenario["rotulos"])
    for x in linhas[:5]:  # 5 trechos com rótulo da LLM (o mesmo valor da regra, para comparar os tamanhos)
        for g in ("risco", "oportunidade", "interesse"):
            x[f"{g}_llm"] = x[g]
        x["fonte"] = "llm"
    comum.gravar_csv(cenario["rotulos"], linhas, list(linhas[0]))
    assert treinar.main(_args(cenario)) == 0
    veredito = '{"risco": "usar", "oportunidade": "nao_usar", "interesse": "nao_usar", "data": "2026-10-12"}'
    assert treinar.main(_com_veredito(cenario, veredito)) == 0
    sem, com = _metadatas(cenario)
    assert com["tamanhos"] == sem["tamanhos"]  # 3-D4: o veredito só é registrado, o rótulo de treino não muda
    n = len(linhas)
    assert com["professora"] == {
        "arquivo": "professora_veredito.json", "data": "2026-10-12",
        "grupos": {"risco": {"veredito": "usar", "rotulos_llm": 5, "rotulos_regra": n - 5},
                   "interesse": {"veredito": "nao_usar", "rotulos_llm": 5, "rotulos_regra": n - 5}},
        "avisos": ["interesse: 5 rótulo(s) da LLM sem veredito 'usar' da professora"]}
    impresso = capsys.readouterr().out
    assert '"interesse": "nao_usar"' in impresso and all(x["texto"] not in impresso for x in linhas)


@pytest.mark.parametrize("conteudo", ["{nao e json segredo", '{"risco": "talvez segredo"}', '["usar"]'])
def test_veredito_invalido_para_sem_mostrar_o_conteudo(cenario, conteudo):
    with pytest.raises(SystemExit) as erro:
        treinar.main(_com_veredito(cenario, conteudo))
    assert "professora_veredito.json" in str(erro.value) and "segredo" not in str(erro.value)
    assert not cenario["candidatos"].exists()
