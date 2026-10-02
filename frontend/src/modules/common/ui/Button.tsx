import type { ButtonHTMLAttributes, FC, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost";
type Size = "sm" | "default" | "lg" | "icon";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50",
  secondary:
    "border border-slate-300 bg-white text-slate-900 hover:bg-slate-50 disabled:opacity-50",
  ghost: "text-slate-600 hover:text-slate-900",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-sm",
  default: "h-10 px-4 text-sm",
  lg: "h-11 px-5 text-base",
  icon: "h-8 w-8",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  children: ReactNode;
}

export const Button: FC<ButtonProps> = ({
  variant = "primary",
  size = "default",
  className = "",
  children,
  ...props
}) => (
  <button
    className={`inline-flex items-center justify-center rounded-md font-medium transition-colors disabled:cursor-not-allowed ${SIZES[size]} ${VARIANTS[variant]} ${className}`}
    {...props}
  >
    {children}
  </button>
);
