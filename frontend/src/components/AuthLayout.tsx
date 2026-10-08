import type { ReactNode } from 'react'

interface Props {
    imagem: string
    headline: string
    descricao: string
    titulo: string
    subtitulo: string
    children: ReactNode
}

export default function AuthLayout({ imagem, headline, descricao, titulo, subtitulo, children }: Props) {
    return (
        <main className="grid min-h-screen lg:grid-cols-[5fr_7fr]">
            <aside className="relative hidden overflow-hidden lg:block">
                <img src={imagem} alt="" className="absolute inset-0 h-full w-full object-cover" />
                <div className="absolute inset-0 bg-brand-navy/100" />
                <div className="relative flex h-full flex-col justify-center gap-4 px-12 text-white">
                    <img src="/images/logo-insightcall.svg" alt="TOTVS InsightCall" className="mb-4 h-7 w-auto self-start" />
                    <h2 className="text-3xl font-bold leading-tight">{headline}</h2>
                    <p className="max-w-xs text-sm leading-relaxed text-white/70">{descricao}</p>
                </div>
            </aside>

            <section className="flex items-center justify-center bg-white px-6 py-10">
                <div className="w-full max-w-sm">
                    <h1 className="text-xl font-bold text-brand-navy">{titulo}</h1>
                    <p className="mt-1 text-xs text-slate-500">{subtitulo}</p>
                    <div className="mt-6">{children}</div>
                </div>
            </section>
        </main>
    )
}