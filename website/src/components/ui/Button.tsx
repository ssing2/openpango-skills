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
  const base = "inline-flex items-center justify-center gap-2 font-medium text-[13px] rounded-lg transition-all";

  const variants = {
    primary: "bg-[#ff4d00] text-white hover:brightness-110",
    secondary: "bg-white text-zinc-900 hover:bg-zinc-100",
    outline: "border border-white/[0.08] text-zinc-400 hover:text-white hover:border-white/[0.16]",
    ghost: "text-zinc-500 hover:text-white",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-[12px]",
    md: "px-4 py-2",
    lg: "px-5 py-2.5",
  };

  const cls = cn(base, variants[variant], sizes[size], className);

  if (href) return <Link href={href} className={cls}>{children}</Link>;
  return <button className={cls} {...props}>{children}</button>;
}
