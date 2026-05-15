"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { normalisePhone } from "@/lib/utils";
import type { SendOtpResponse } from "@/lib/types";

export default function PhonePage() {
  const router = useRouter();
  const { toast } = useToast();
  const { setPendingPhone } = useAuthStore();

  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handlePhoneChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value.replace(/\D/g, "").slice(0, 11);
    setPhone(val);
    if (error) setError("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (phone.length < 10) {
      setError("Enter a valid Nigerian phone number");
      return;
    }
    setLoading(true);
    try {
      const normalised = normalisePhone(phone);
      await api.post<SendOtpResponse>("/auth/send-otp", { phone: normalised });
      setPendingPhone(normalised);
      router.push("/auth/verify");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Something went wrong", "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-dvh flex-col">
      {/* Hero */}
      <div className="bg-hero-pattern flex flex-col items-center justify-center px-6 pt-20 pb-14 relative overflow-hidden">
        <div className="absolute inset-0 bg-card-shine pointer-events-none" />
        <div className="relative mb-5 flex h-20 w-20 items-center justify-center rounded-3xl bg-white/10 border border-white/20 shadow-glass">
          <svg viewBox="0 0 48 48" className="h-12 w-12" aria-hidden>
            <circle cx="24" cy="24" r="22" fill="rgb(255 255 255 / 0.15)" />
            <path d="M12 24 Q24 8 36 24 Q24 40 12 24Z" fill="white" opacity="0.9" />
            <circle cx="24" cy="24" r="5" fill="white" />
          </svg>
        </div>
        <h1 className="text-4xl font-extrabold text-white tracking-tight">EcoNet</h1>
        <p className="mt-2 text-center text-sm text-white/70 max-w-[220px]">
          Your community financial identity
        </p>

        {/* Stats row */}
        <div className="mt-8 flex gap-6">
          {[["₦0 fees", "Transfers"], ["AI-powered", "Matching"], ["CBN compliant", "Identity"]].map(([val, lbl]) => (
            <div key={lbl} className="text-center">
              <p className="text-xs font-bold text-white/90">{val}</p>
              <p className="text-[10px] text-white/50">{lbl}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Form card */}
      <div className="flex-1 rounded-t-3xl bg-background -mt-4 px-6 pt-8 pb-8">
        <h2 className="text-xl font-bold text-foreground">Get started</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Enter your Nigerian phone number to continue
        </p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-1 flex-col gap-4">
          <Input
            label="Phone number"
            type="tel"
            inputMode="numeric"
            placeholder="0812 345 6789"
            value={phone}
            onChange={handlePhoneChange}
            error={error}
            leftAddon={
              <span className="text-sm font-medium">🇳🇬</span>
            }
            autoFocus
          />

          <Button
            type="submit"
            className="w-full mt-2"
            size="lg"
            loading={loading}
            disabled={phone.length < 10}
          >
            Send verification code
          </Button>

          <p className="text-center text-xs text-muted-foreground">
            We&apos;ll send a code via SMS or WhatsApp
          </p>
        </form>

        <div className="mt-8 rounded-2xl bg-accent/40 border border-accent p-4">
          <p className="text-xs font-semibold text-primary mb-1">About EcoNet</p>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Built for the GTCO Squad Hackathon — turning informal economic activity into a trusted financial identity.
          </p>
        </div>
      </div>
    </div>
  );
}
