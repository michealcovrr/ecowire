import * as React from "react";
import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "secondary" | "accent" | "gold" | "success" | "destructive" | "warning" | "outline";

const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-primary text-primary-foreground",
  secondary: "bg-secondary text-secondary-foreground",
  accent: "bg-accent text-accent-foreground",
  gold: "bg-gold-light text-gold-foreground",
  success: "bg-success-light text-success",
  destructive: "bg-destructive-light text-destructive",
  warning: "bg-warning-light text-warning",
  outline: "border border-border text-foreground bg-transparent",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold leading-tight",
        variantClasses[variant],
        className
      )}
      {...props}
    />
  );
}
