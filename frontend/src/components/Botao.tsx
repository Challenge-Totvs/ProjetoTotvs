import type { ButtonHTMLAttributes } from 'react'

export default function Botao(props: ButtonHTMLAttributes<HTMLButtonElement>) {
    return (
        <button
            {...props}
            className="w-full rounded-lg bg-brand-cyan px-4 py-2.5 text-xs font-semibold text-brand-navy transition hover:bg-brand-cyan-hover focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-brand-cyan/40 disabled:cursor-not-allowed disabled:opacity-60"
        />
    )
}