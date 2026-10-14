"""Fluxo ponta a ponta pelo backend, só HTTP (sem navegador), para ensaio de integração.

login -> cliente -> reunião -> transcrição -> analisar -> ler a reunião. Cria um cliente novo a cada execução
(evita o 409 de transcrição duplicada). Imprime só status, ids, contagens, motor e segundos; nunca texto.

    python scripts/fluxo_integracao.py                                  # transcrição curta embutida
    python scripts/fluxo_integracao.py --pedido arquivo-pedido-v3.json  # turnos de um pedido v3 (ex.: o sintético grande)

Usuário: --email/--senha (padrão integracao@insightcall.test); se o login falhar, registra a conta.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

# Transcrição SINTÉTICA, inventada aqui: um risco (preço/concorrente), uma oportunidade e um compromisso.
CURTA = [
    (1, "Bom dia, obrigado por reservar o horário. Queria entender como está o uso do módulo financeiro."),
    (2, "Bom dia. O financeiro está rodando, mas o preço da renovação veio bem acima do que a diretoria esperava."),
    (1, "Entendo. O que pesou mais na comparação?"),
    (2, "Recebemos uma proposta de outro fornecedor com valor menor e a diretoria pediu para avaliar a troca."),
    (1, "Posso montar uma condição comercial nova. Mando a proposta revisada até sexta-feira."),
    (2, "Combinado. E temos interesse em expandir para o módulo de estoque no próximo semestre."),
    (1, "Ótimo, incluo o estoque na proposta e agendamos uma demonstração com o time de operação."),
]


def texto_de(turnos) -> str:
    return "\n".join(f"[LOCUTOR {loc}] {fala}" for loc, fala in turnos)


def turnos_do_pedido(caminho: str):
    with open(caminho, encoding="utf-8") as arq:
        return [(t["locutor"], t["texto"]) for t in json.load(arq)["turnos"]]


def hora_da_reuniao(agora: datetime) -> str:
    """09:00 de hoje no fuso local. O backend grava a hora em UTC (bug de fuso, ver integracao-14-10.md):
    depois das 21h de Brasília, "agora - 1 h" vira o dia seguinte e a reunião é recusada como futura."""
    return agora.replace(hour=9, minute=0, second=0, microsecond=0).isoformat(timespec="seconds")


def chamar(base: str, metodo: str, caminho: str, corpo=None, token=None, timeout=180):
    dados = None if corpo is None else json.dumps(corpo).encode("utf-8")
    pedido = urllib.request.Request(base + caminho, data=dados, method=metodo)
    pedido.add_header("Content-Type", "application/json")
    if token:
        pedido.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(pedido, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as erro:
        try:
            return erro.code, json.loads(erro.read() or b"null")
        except ValueError:
            return erro.code, None


def resumo_reuniao(detalhe: dict) -> dict:
    """Só números e rótulos: nada de texto de transcrição ou de citação."""
    analise = detalhe.get("analise") or {}
    temas = detalhe.get("temas") or []
    return {
        "status": detalhe.get("status"),
        "temTranscricao": detalhe.get("temTranscricao"),
        "turnos": detalhe.get("turnos"),
        "motor": analise.get("motor"),
        "tentativas": [(t.get("motor"), t.get("ok")) for t in analise.get("tentativas") or []],
        "score": analise.get("score"),
        "temas": len(temas),
        "temasComCitacao": sum(1 for t in temas if t.get("citacao")),
        "compromissos": len(detalhe.get("compromissos") or []),
    }


def entrar(base: str, email: str, senha: str) -> str:
    status, corpo = chamar(base, "POST", "/api/auth/login", {"email": email, "senha": senha})
    if status != 200:
        chamar(base, "POST", "/api/auth/register", {"nome": "Integracao Teste", "email": email, "senha": senha})
        status, corpo = chamar(base, "POST", "/api/auth/login", {"email": email, "senha": senha})
    if status != 200:
        raise SystemExit(f"login falhou: HTTP {status}")
    return corpo["token"]


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://localhost:8080")
    p.add_argument("--email", default="integracao@insightcall.test")
    p.add_argument("--senha", default="integracao123")
    p.add_argument("--pedido", help="pedido v3 (JSON) de onde tirar os turnos")
    p.add_argument("--reuniao", type=int, help="pula a criação e só reanalisa a transcrição desta reunião")
    p.add_argument("--transcricao", type=int, help="id da transcrição para reanalisar (com --reuniao)")
    args = p.parse_args(argv)

    base = args.base.rstrip("/")
    token = entrar(base, args.email, args.senha)
    marca = datetime.now().strftime("%H%M%S")

    if args.reuniao and args.transcricao:
        reuniao_id, transcricao_id = args.reuniao, args.transcricao
    else:
        st, cliente = chamar(base, "POST", "/api/clientes", {
            "nome": f"Cliente Sintetico {marca}", "segmento": "Varejo",
            "contato": {"nome": "Contato Sintetico", "cargo": "Diretor"}}, token)
        print(f"cliente: HTTP {st}")
        quando = hora_da_reuniao(datetime.now().astimezone())
        st, reuniao = chamar(base, "POST", "/api/reunioes", {
            "clienteId": cliente["id"], "titulo": f"Integracao {marca}", "dataHora": quando,
            "duracaoMin": 30, "status": "aguardando"}, token)
        print(f"reuniao: HTTP {st} id={(reuniao or {}).get('id')} codigo={(reuniao or {}).get('codigo')}")
        reuniao_id = reuniao["id"]
        turnos = turnos_do_pedido(args.pedido) if args.pedido else CURTA
        conteudo = texto_de(turnos)
        st, enviada = chamar(base, "POST", f"/api/reunioes/{reuniao_id}/transcricao",
                             {"conteudo": conteudo, "formatoOrigem": "COLADO"}, token)
        print(f"transcricao: HTTP {st} caracteres={len(conteudo)} turnos={len(turnos)}")
        transcricao_id = enviada["transcricaoId"]

    inicio = time.perf_counter()
    st, analise = chamar(base, "POST", f"/api/transcricoes/{transcricao_id}/analisar", token=token)
    segundos = time.perf_counter() - inicio
    if st == 200:
        print(f"analisar: HTTP {st} em {segundos:.1f} s motor={analise['motor']} "
              f"tentativas={[(t['motor'], t['ok']) for t in analise['tentativas']]} "
              f"novos={analise['novos']} compromissos={analise['compromissos']}")
    else:
        print(f"analisar: HTTP {st} em {segundos:.1f} s codigo={(analise or {}).get('codigo')}")

    st, detalhe = chamar(base, "GET", f"/api/reunioes/{reuniao_id}", token=token)
    print(f"reuniao lida: HTTP {st} {json.dumps(resumo_reuniao(detalhe or {}), ensure_ascii=False)}")
    print(f"ids: reuniao={reuniao_id} transcricao={transcricao_id}")
    return 0 if st == 200 else 1


if __name__ == "__main__":
    sys.exit(main())
