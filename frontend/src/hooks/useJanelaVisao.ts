import { useState } from "react";

/**
 * Janela de visualização (30/60/90 dias): estado local da página, inicializado com a janela
 * do time e sincronizado com ela até a pessoa escolher outra no seletor. Nunca grava na config do time.
 */
export function useJanelaVisao(janelaDoTime: number) {
  const [janela, setJanela] = useState(janelaDoTime);
  const [base, setBase] = useState(janelaDoTime);
  if (base !== janelaDoTime) {
    setBase(janelaDoTime);
    setJanela(janelaDoTime);
  }
  return [janela, setJanela] as const;
}
