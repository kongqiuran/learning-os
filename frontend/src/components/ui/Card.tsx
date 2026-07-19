import type { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends HTMLAttributes<HTMLElement> {
  children: ReactNode
}

export function Card({ children, className = '', ...props }: CardProps) {
  return (
    <article
      className={`rounded-2xl border border-stone-200 bg-[#fffdfa] shadow-[0_1px_3px_rgba(28,25,23,0.035)] ${className}`}
      {...props}
    >
      {children}
    </article>
  )
}
