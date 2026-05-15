"use client";

import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { cn } from "@/lib/utils";

interface TopBarProps {
  title?: string;
  subtitle?: string;
  onBack?: () => void;
  showBack?: boolean;
  right?: React.ReactNode;
  transparent?: boolean;
  className?: string;
}

export function TopBar({
  title,
  subtitle,
  onBack,
  showBack = false,
  right,
  transparent = false,
  className,
}: TopBarProps) {
  const router = useRouter();

  function handleBack() {
    if (onBack) onBack();
    else router.back();
  }

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-3 min-h-[56px]",
        !transparent && "bg-white border-b border-border/60",
        className
      )}
    >
      {showBack && (
        <button
          onClick={handleBack}
          className="flex h-9 w-9 items-center justify-center rounded-full hover:bg-muted transition-colors flex-shrink-0"
        >
          <ChevronLeft className="h-5 w-5 text-foreground" />
        </button>
      )}

      <div className="flex-1 min-w-0">
        {title && (
          <h1 className="text-base font-bold text-foreground truncate">{title}</h1>
        )}
        {subtitle && (
          <p className="text-xs text-muted-foreground truncate">{subtitle}</p>
        )}
      </div>

      {right && (
        <div className="flex items-center gap-2 flex-shrink-0">{right}</div>
      )}
    </div>
  );
}
