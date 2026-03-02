import React from "react";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  href?: string;
}

export function Button({
  className,
  variant = "primary",
  size = "md",
  children,
  href,
  ...props
}: ButtonProps) {
  const base = "relative font-bold text-xs tracking-[0.15em] uppercase transition-all inline-flex items-center justify-center gap-2";

  const variants = {
    primary: "bg-[#ff3e00] text-white shadow-[4px_4px_0_rgba(255,255,255,0.15)] hover:-translate-y-0.5 hover:-translate-x-0.5 hover:shadow-[6px_6px_0_#ff3e00]",
    secondary: "bg-white text-black shadow-[4px_4px_0_#ff3e00] hover:-translate-y-0.5 hover:-translate-x-0.5 hover:shadow-[6px_6px_0_#ff3e00]",
    outline: "border-2 border-zinc-700 text-zinc-300 hover:border-[#ff3e00] hover:text-[#ff3e00]",
    ghost: "text-zinc-500 hover:text-white",
  };

  const sizes = {
    sm: "px-4 py-2",
    md: "px-6 py-3",
    lg: "px-8 py-4",
  };

  const cls = cn(base, variants[variant], sizes[size], className);

  if (href) {
    return <Link href={href} className={cls}>{children}</Link>;
  }

  return <button className={cls} {...props}>{children}</button>;
}
