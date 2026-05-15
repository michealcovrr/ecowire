"use client";

import { useRef, useState, useCallback } from "react";
import { cn } from "@/lib/utils";

interface OtpInputProps {
  length?: number;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function OtpInput({ length = 6, value, onChange, disabled }: OtpInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [focused, setFocused] = useState(false);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const raw = e.target.value.replace(/\D/g, "").slice(0, length);
      onChange(raw);
    },
    [length, onChange]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Backspace" && value.length === 0) return;
    },
    [value]
  );

  const slots = Array.from({ length }, (_, i) => ({
    char: value[i] ?? null,
    isActive: focused && i === Math.min(value.length, length - 1),
  }));

  return (
    <div
      className="relative flex gap-2 cursor-text"
      onClick={() => inputRef.current?.focus()}
    >
      {/* Hidden real input */}
      <input
        ref={inputRef}
        type="tel"
        inputMode="numeric"
        pattern="[0-9]*"
        maxLength={length}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        disabled={disabled}
        className="absolute inset-0 opacity-0 w-full h-full cursor-text"
        autoComplete="one-time-code"
        aria-label="OTP input"
      />

      {/* Visual slots */}
      {slots.map(({ char, isActive }, i) => (
        <div
          key={i}
          className={cn(
            "relative flex h-14 w-12 items-center justify-center rounded-xl border-2 text-2xl font-bold select-none transition-all",
            isActive
              ? "border-primary shadow-[0_0_0_3px_rgba(21,128,61,0.15)]"
              : value.length > i
              ? "border-primary/40 bg-green-50"
              : "border-gray-200 bg-white"
          )}
        >
          {char ?? (
            isActive ? (
              <div className="h-6 w-0.5 animate-pulse bg-primary" />
            ) : (
              <span className="text-gray-200">·</span>
            )
          )}
        </div>
      ))}
    </div>
  );
}
