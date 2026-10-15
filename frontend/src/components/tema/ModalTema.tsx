/* Pop-up dedicado para abrir um tema levantado fora da página do cliente (ex.: a partir
   de um chip clicável na lista de Clientes). Mostra o mesmo conteúdo do inspetor do tema —
   onde a leitura foi levantada e por quê, recorrência, aviso de semelhança com um "não
   procede" anterior, e a lista "Onde apareceu" com um botão direto para a reunião
   específica em que o tema foi citado — sem navegar para outra tela. Se o usuário puder
   agir neste tema (vendedor dono do cliente), os botões de ação aparecem aqui também. */

import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { Tema } from "../../types/api";
import { rotas } from "../../lib/rotas";
import { InspetorTema } from "../cliente/InspetorTema";
import { btn } from "../ui/classes";
import { Modal } from "../ui/Sobrepostos";

export function ModalTema({ tema, podeAgir, onFechar }: { tema: Tema; podeAgir: boolean; onFechar: () => void }) {
  const navigate = useNavigate();
  const [contextoAberto, setContextoAberto] = useState<string | null>(null);
  const n = tema.citacoes.length;

  return (
    <Modal titulo={tema.titulo} descricao={`${tema.clienteNome} · levantado em ${n === 1 ? "1 reunião" : `${n} reuniões`}`} onFechar={onFechar} largura={620}>
      <InspetorTema tema={tema} podeAgir={podeAgir} contextoAberto={contextoAberto} setContextoAberto={setContextoAberto} semTitulo />
      <div className="mt-4 flex justify-end border-t border-linha pt-3">
        <button
          type="button"
          className={btn()}
          onClick={() => {
            onFechar();
            navigate(rotas.cliente(tema.clienteId, tema.id));
          }}
        >
          Abrir o cliente
          <ArrowRight size={14} aria-hidden="true" />
        </button>
      </div>
    </Modal>
  );
}
