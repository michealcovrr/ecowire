import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  leftAddon?: React.ReactNode;
  rightAddon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, hint, error, leftAddon, rightAddon, type, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label className="block text-sm font-semibold text-foreground/70">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftAddon && (
            <div className="absolute left-3.5 flex items-center text-muted-foreground pointer-events-none">
              {leftAddon}
            </div>
          )}
          <input
            type={type}
            className={cn(
              "w-full h-12 rounded-xl border-2 border-border bg-white px-4 text-sm text-foreground",
              "placeholder:text-muted-foreground/60",
              "focus:border-primary focus:outline-none focus:ring-0",
              "transition-colors duration-150",
              "disabled:bg-muted disabled:text-muted-foreground",
              leftAddon && "pl-11",
              rightAddon && "pr-11",
              error && "border-destructive focus:border-destructive",
              className
            )}
            ref={ref}
            {...props}
          />
          {rightAddon && (
            <div className="absolute right-3.5 flex items-center text-muted-foreground">
              {rightAddon}
            </div>
          )}
        </div>
        {hint && !error && (
          <p className="text-xs text-muted-foreground">{hint}</p>
        )}
        {error && (
          <p className="text-xs text-destructive font-medium">{error}</p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };
