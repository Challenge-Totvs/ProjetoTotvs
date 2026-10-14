/* Buscar no histórico do cliente: caixa de busca e os trechos de reuniões anteriores mais parecidos. */

import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ExternalLink, Search } from "lucide-react";
import { buscarEvidencias } from "../../api/clientes";
import { mensagemDeErro } from "../../api/http";
import { Aviso, Carregando, Secao, Vazio } from "../ui/base";
import { btn, busca as classeBusca, linkForte } from "../ui/classes";
import { fmtDataAno, fmtHora, paraData } from "../../lib/datas";
import { rotas } from "../../lib/rotas";
import type { Id, RespostaEvidencias } from "../../types/api";

const MAXIMO_CONSULTA = 500; // igual ao limite do backend (evidencias.md §2)

export function BuscaHistorico({ clienteId }: { clienteId: Id }) {
  const navigate = useNavigate();
  const [consulta, setConsulta] = useState("");
  const [buscada, setBuscada] = useState<string | null>(null);
  const [resposta, setResposta] = useState<RespostaEvidencias | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  // Ignora a resposta de uma busca antiga se outra já começou depois.
  const versao = useRef(0);

  const buscar = async (e: React.FormEvent) => {
    e.preventDefault();
    const termo = consulta.trim();
    if (!termo) return;
    const minha = ++versao.current;
    setCarregando(true);
    setErro(null);
    try {
      const r = await buscarEvidencias(clienteId, termo);
      if (minha !== versao.current) return;
      setResposta(r);
      setBuscada(termo);
    } catch (err) {
      if (minha === versao.current) setErro(mensagemDeErro(err, "Não foi possível buscar. Tente de novo."));
    } finally {
      if (minha === versao.current) setCarregando(false);
    }
  };

  return (
    <Secao id="busca-historico" titulo="Buscar no histórico" sub="Procure um assunto nas conversas anteriores com este cliente.">
      <form onSubmit={(e) => void buscar(e)} className="flex flex-wrap items-center gap-2.5" role="search">
        <label className={classeBusca}>
          <Search size={14} aria-hidden="true" className="text-faint" />
          <input
            value={consulta}
            onChange={(e) => setConsulta(e.target.value)}
            maxLength={MAXIMO_CONSULTA}
            placeholder="Ex.: prazo de entrega, preço, suporte"
            aria-label="Buscar no histórico do cliente"
          />
        </label>
        <button type="submit" className={btn({ primario: true })} disabled={carregando || !consulta.trim()}>
          Buscar
        </button>
      </form>

      <div className="mt-3" aria-live="polite">
        {carregando && <Carregando texto="Buscando…" />}
        {!carregando && erro && <Aviso tom="erro">{erro}</Aviso>}
        {!carregando && !erro && resposta?.aviso && <Aviso tom="atencao">{resposta.aviso}</Aviso>}
        {!carregando && !erro && resposta && !resposta.aviso && resposta.evidencias.length === 0 && (
          <Vazio titulo="Nada encontrado" texto={`Nenhum trecho parecido com “${buscada}”. Tente outras palavras.`} />
        )}
        {!carregando && !erro && resposta && resposta.evidencias.length > 0 && (
          <ul className="m-0 grid list-none gap-2 p-0">
            {resposta.evidencias.map((ev) => {
              const data = paraData(ev.data);
              return (
                <li key={`${ev.reuniaoId}-${ev.turno}`} className="rounded-[10px] border border-linha bg-nevoa p-3">
                  <blockquote className="m-0 text-[13.5px] leading-[1.5] text-ink">“{ev.texto}”</blockquote>
                  <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12.5px] text-ardosia">
                    <span className="tabular-nums">
                      {fmtDataAno(data)}, {fmtHora(data)}
                    </span>
                    <button type="button" className={`${linkForte} inline-flex items-center gap-1`} onClick={() => navigate(rotas.reuniao(ev.reuniaoId, ev.turno))}>
                      <ExternalLink size={12} aria-hidden="true" />
                      Abrir na reunião
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </Secao>
  );
}
