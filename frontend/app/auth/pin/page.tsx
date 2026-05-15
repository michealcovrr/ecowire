"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { OtpInput } from "@/components/ui/otp-input";
import { useToast } from "@/components/ui/toast";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { formatPhone } from "@/lib/utils";
import { ChevronLeft, Lock } from "lucide-react";
import type { AuthSuccessResponse } from "@/lib/types";

export default function PinPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { pendingPhone, setToken, setUser, setSquadAccount, setQrCode } = useAuthStore();

  const [pin, setPin] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!pendingPhone) router.replace("/auth/phone");
  }, [pendingPhone, router]);

  useEffect(() => {
    if (pin.length === 6) handleLogin(pin);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pin]);

  async function handleLogin(enteredPin: string) {
    if (loading) return;
    setLoading(true);
    try {
      const res = await api.post<AuthSuccessResponse>("/auth/login", {
        phone: pendingPhone,
        pin: enteredPin,
      });
      const d = res.data;
      setToken(d.token);
      setUser(d.user);
      setSquadAccount(d.squad_account_number ?? null, d.squad_bank_name ?? null);
      setQrCode(d.qr_code ?? null);
      router.replace("/dashboard");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Invalid PIN", "error");
      setPin("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      {/* Top */}
      <div className="bg-hero-pattern px-5 pt-12 pb-14">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1.5 text-sm text-white/70 hover:text-white mb-8"
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </button>

        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15 border border-white/20 mb-4">
          <Lock className="h-7 w-7 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white">Welcome back!</h2>
        <p className="mt-1 text-sm text-white/65">
          Enter your PIN for{" "}
          <span className="font-semibold text-white">{formatPhone(pendingPhone)}</span>
        </p>
      </div>

      {/* PIN entry */}
      <div className="flex-1 rounded-t-3xl bg-background -mt-4 px-6 pt-8 pb-8 flex flex-col">
        <p className="text-sm font-semibold text-foreground mb-6">Enter your 6-digit PIN</p>

        <div className="flex justify-center">
          <OtpInput
            length={6}
            value={pin}
            onChange={setPin}
            disabled={loading}
          />
        </div>

        {loading && (
          <div className="mt-8 flex flex-col items-center gap-2">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <p className="text-sm text-muted-foreground">Signing you in…</p>
          </div>
        )}

        <div className="mt-auto pt-8 text-center space-y-3">
          <p className="text-sm text-muted-foreground">
            Not you?{" "}
            <button
              onClick={() => router.replace("/auth/phone")}
              className="font-semibold text-primary hover:underline"
            >
              Use a different number
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
