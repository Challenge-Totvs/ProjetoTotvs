/* Campo das telas de acesso: rótulo, mostrar/ocultar senha, aviso de Caps Lock, erro e dica. */

import { useState, type KeyboardEvent, type Ref } from "react";
import { Eye, EyeOff } from "lucide-react";
import { input } from "../../components/ui/classes";
import { cx } from "../../lib/formato";

export function CampoAcesso({
  id,
  label,
  value,
  onChange,
  placeholder,
  autoComplete,
  erro,
  dica,
  dicaOk,
  inputRef,
  autoFocus,
  senha,
  readOnly,
  onBlur,
  type = "text",
}: {
  id: string;
  label: string;
  value: string;
  onChange?: (v: string) => void;
  placeholder?: string;
  autoComplete?: string;
  erro?: string | null;
  dica?: string | null;
  dicaOk?: boolean;
  inputRef?: Ref<HTMLInputElement>;
  autoFocus?: boolean;
  senha?: boolean;
  readOnly?: boolean;
  onBlur?: () => void;
  type?: string;
}) {
  const [ver, setVer] = useState(false);
  const [caps, setCaps] = useState(false);
  const tipo = senha ? (ver ? "text" : "password") : type;
  const descr =
    [erro ? `${id}-erro` : null, dica && !erro ? `${id}-dica` : null, caps ? `${id}-caps` : null].filter(Boolean).join(" ") || undefined;
  const verCaps = (e: KeyboardEvent<HTMLInputElement>) => {
    if (senha && e.getModifierState) setCaps(e.getModifierState("CapsLock"));
  };
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-[13px] font-medium text-ink">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          ref={inputRef}
          className={cx(input, senha ? "pr-[46px]" : "", readOnly ? "bg-nevoa! text-ardosia!" : "")}
          type={tipo}
          value={value}
          onChange={(e) => onChange && onChange(e.target.value)}
          onBlur={onBlur}
          onKeyDown={verCaps}
          onKeyUp={verCaps}
          placeholder={placeholder}
          autoComplete={autoComplete}
          autoFocus={autoFocus}
          readOnly={readOnly}
          aria-invalid={erro ? "true" : "false"}
          aria-describedby={descr}
        />
        {senha && (
          <button
            type="button"
            onClick={() => setVer((v) => !v)}
            aria-label={ver ? "Ocultar senha" : "Mostrar senha"}
            aria-pressed={ver}
            className="absolute top-1.5 right-1.5 flex h-8 w-8 items-center justify-center rounded-md text-ardosia"
          >
            {ver ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
      {caps && (
        <span id={`${id}-caps`} className="text-xs text-atencao">
          Caps Lock ativado
        </span>
      )}
      {erro && (
        <span id={`${id}-erro`} className="text-xs leading-[1.4] text-critico">
          {erro}
        </span>
      )}
      {dica && !erro && (
        <span id={`${id}-dica`} className={cx("text-xs leading-[1.4]", dicaOk ? "text-resolvido" : "text-faint")}>
          {dica}
        </span>
      )}
    </div>
  );
}

