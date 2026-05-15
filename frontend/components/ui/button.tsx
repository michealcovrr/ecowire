import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonVariant =
  | "default"
  | "secondary"
  | "outline"
  | "ghost"
  | "destructive"
  | "gold"
  | "whatsapp";
type ButtonSize = "default" | "sm" | "lg" | "icon";

const variantClasses: Record<ButtonVariant, string> = {
  default:
    "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm active:bg-primary/80",
  secondary:
    "bg-secondary text-secondary-foreground hover:bg-secondary/80 active:bg-secondary/60",
  outline:
    "border-2 border-primary text-primary bg-transparent hover:bg-primary/5 active:bg-primary/10",
  ghost:
    "text-primary hover:bg-primary/8 active:bg-primary/12",
  destructive:
    "bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-sm active:bg-destructive/80",
  gold:
    "bg-gold text-gold-foreground hover:bg-gold/90 shadow-sm active:bg-gold/80",
  whatsapp:
    "bg-[#25D366] text-white hover:bg-[#20bc5a] shadow-sm active:bg-[#1aac52]",
};

const sizeClasses: Record<ButtonSize, string> = {
  default: "h-12 px-6 text-sm font-semibold",
  sm: "h-9 px-4 text-xs font-semibold",
  lg: "h-14 px-8 text-base font-bold",
  icon: "h-10 w-10",
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", loading, children, disabled, ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl",
          "ring-offset-2 transition-all duration-150",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
          "disabled:pointer-events-none disabled:opacity-50",
          "active:scale-[0.97]",
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <>
            <svg
              className="h-4 w-4 animate-spin"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            {children}
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);
Button.displayName = "Button";

export { Button };
