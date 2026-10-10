/* Leitura do arquivo .txt da transcrição, igual à demo. */

/**
 * Lê o arquivo como bytes e tenta UTF-8 estrito; se tiver byte inválido,
 * cai para Windows-1252 (arquivos salvos no Bloco de Notas antigo).
 */
export function lerArquivoTexto(arquivo: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const leitor = new FileReader();
    leitor.onload = () => {
      const buf = leitor.result as ArrayBuffer;
      try {
        resolve(new TextDecoder("utf-8", { fatal: true }).decode(buf));
      } catch {
        resolve(new TextDecoder("windows-1252").decode(buf));
      }
    };
    leitor.onerror = () => reject(leitor.error);
    leitor.readAsArrayBuffer(arquivo);
  });
}

/** Data e hora do formulário (dia local) no formato ISO com o fuso do navegador: "2026-10-09T15:00:00-03:00". */
export function dataHoraLocalISO(data: string, hora: string): string {
  const [a, m, d] = data.split("-").map(Number);
  const [h, mi] = (hora || "10:00").split(":").map(Number);
  const local = new Date(a, m - 1, d, h, mi);
  // getTimezoneOffset devolve minutos com o sinal invertido (Brasil = +180).
  const fuso = -local.getTimezoneOffset();
  const dois = (n: number) => String(n).padStart(2, "0");
  const sinal = fuso >= 0 ? "+" : "-";
  const abs = Math.abs(fuso);
  return `${data}T${dois(h)}:${dois(mi)}:00${sinal}${dois(Math.floor(abs / 60))}:${dois(abs % 60)}`;
}

/** Espera alguns milissegundos (usado para dar ritmo às etapas do andamento). */
export const esperar = (ms: number) => new Promise<void>((ok) => setTimeout(ok, ms));
