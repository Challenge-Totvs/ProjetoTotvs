import { http } from "./http";
import type {
  EnviarTranscricaoRequest,
  EnviarTranscricaoResponse,
  Id,
  NovaReuniaoRequest,
  ReuniaoDetalhe,
  ResultadoAnalisarResponse,
  TurnoTranscricao,
} from "../types/api";

/** GET /api/reunioes/{id} — reunião com análise, temas, compromissos e métricas. */
export async function buscarReuniao(id: Id): Promise<ReuniaoDetalhe> {
  const { data } = await http.get<ReuniaoDetalhe>(`/api/reunioes/${id}`);
  return data;
}

/** GET /api/reunioes/{id}/transcricao?versao= — turnos no texto original ou como a LLM recebeu. */
export async function buscarTranscricao(id: Id, versao: "original" | "llm"): Promise<TurnoTranscricao[]> {
  const { data } = await http.get<TurnoTranscricao[]>(`/api/reunioes/${id}/transcricao`, { params: { versao } });
  return data;
}

/** POST /api/reunioes — cria a reunião (já realizada, aguardando transcrição). */
export async function criarReuniao(dados: NovaReuniaoRequest): Promise<{ id: Id }> {
  const { data } = await http.post<{ id: Id }>("/api/reunioes", dados);
  return data;
}

/** POST /api/reunioes/{id}/transcricao — grava o texto. 409 se for duplicata. */
export async function enviarTranscricao(reuniaoId: Id, dados: EnviarTranscricaoRequest): Promise<EnviarTranscricaoResponse> {
  const { data } = await http.post<EnviarTranscricaoResponse>(`/api/reunioes/${reuniaoId}/transcricao`, dados);
  return data;
}

/** POST /api/transcricoes/{id}/analisar — roda a cadeia de motores (síncrono, até 120 s). */
export async function analisarTranscricao(transcricaoId: Id, signal?: AbortSignal): Promise<ResultadoAnalisarResponse> {
  const { data } = await http.post<ResultadoAnalisarResponse>(`/api/transcricoes/${transcricaoId}/analisar`, null, {
    signal,
    timeout: 130000,
  });
  return data;
}
