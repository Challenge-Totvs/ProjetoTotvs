import { useCallback, useEffect, useRef, useState } from "react";
import { mensagemDeErro } from "../api/http";

export interface EstadoApi<T> {
  dados: T | null;
  erro: string | null;
  carregando: boolean;
  /** Busca de novo, mantendo os dados atuais na tela enquanto carrega. */
  recarregar: () => Promise<void>;
  /** Troca os dados localmente (ex.: depois de uma ação que já devolveu o item novo). */
  setDados: (fn: (atual: T | null) => T | null) => void;
}

/**
 * Busca dados de uma função da pasta api/ e guarda o resultado.
 * `deps` funciona como no useEffect: muda o valor, busca de novo.
 */
export function useApi<T>(buscar: () => Promise<T>, deps: unknown[]): EstadoApi<T> {
  const [dados, setDadosState] = useState<T | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const buscarRef = useRef(buscar);
  buscarRef.current = buscar;
  // Evita gravar a resposta de uma busca antiga se outra já começou depois.
  const versao = useRef(0);

  const recarregar = useCallback(async () => {
    const minha = ++versao.current;
    setCarregando(true);
    try {
      const resultado = await buscarRef.current();
      if (minha === versao.current) {
        setDadosState(resultado);
        setErro(null);
      }
    } catch (e) {
      if (minha === versao.current) setErro(mensagemDeErro(e, "Não foi possível carregar os dados."));
    } finally {
      if (minha === versao.current) setCarregando(false);
    }
  }, []);

  useEffect(() => {
    void recarregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  const setDados = useCallback((fn: (atual: T | null) => T | null) => setDadosState((d) => fn(d)), []);

  return { dados, erro, carregando, recarregar, setDados };
}
