import type { InputHTMLAttributes } from 'react'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
    label: string
}

export default function Campo({ label, ...props }: Props) {
    return (
        <label className="block">
            <span className="mb-1.5 block text-xs font-semibold text-brand-navy">{label}</span>
            <input
                {...props}
                className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-brand-navy outline-none transition placeholder:text-slate-400 focus:border-brand-cyan focus:bg-white focus:ring-4 focus:ring-brand-cyan/20"
            />
        </label>
    )
}