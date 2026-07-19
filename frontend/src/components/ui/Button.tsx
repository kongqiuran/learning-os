import type { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'ai' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: ButtonVariant
  fullWidth?: boolean
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'border-teal-700 bg-teal-700 text-white hover:bg-teal-800 focus-visible:ring-teal-100',
  secondary:
    'border-stone-200 bg-white text-stone-700 hover:border-stone-300 hover:bg-stone-50 focus-visible:ring-stone-200',
  ghost: 'border-transparent bg-transparent text-stone-600 hover:bg-stone-100 focus-visible:ring-stone-200',
  ai: 'border-teal-700 bg-teal-700 text-white hover:bg-teal-800 focus-visible:ring-teal-100',
  danger: 'border-red-600 bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-200',
}

export function Button({
  children,
  variant = 'primary',
  fullWidth = false,
  className = '',
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-xl border px-4 py-2 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-4 disabled:cursor-not-allowed disabled:opacity-50 ${variantStyles[variant]} ${fullWidth ? 'w-full' : ''} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
