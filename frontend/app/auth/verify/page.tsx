"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { OtpInput } from "@/components/ui/otp-input";
import { useToast } from "@/components/ui/toast";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { formatPhone } from "@/lib/utils";
import { ChevronLeft, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { VerifyOtpResponse } from "@/lib/types";

export default function VerifyPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { pendingPhone, setPendingTempToken, setToken, setUser, setSquadAccount, setQrCode } =
    useAuthStore();

  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendCountdown, setResendCountdown] = useState(30);

  useEffect(() => {
    if (!pendingPhone) router.replace("/auth/phone");
  }, [pendingPhone, router]);

  useEffect(() => {
    if (resendCountdown <= 0) return;
    const t = setTimeout(() => setResendCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [resendCountdown]);

  useEffect(() => {
    if (code.length === 6) handleVerify(code);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code]);

  async function handleVerify(enteredCode: string) {
    if (loading) return;
    setLoading(true);
    try {
      const res = await api.post<VerifyOtpResponse>("/auth/verify-otp", {
        phone: pendingPhone,
        code: enteredCode,
      });
      const d = res.data;
      if (d.exists && d.token && d.user) {
        setToken(d.token);
        setUser(d.user);
        setSquadAccount(d.squad_account_number ?? null, d.squad_bank_name ?? null);
        setQrCode(d.qr_code ?? null);
        router.replace("/dashboard");
      } else if (!d.exists && d.temp_token) {
        setPendingTempToken(d.temp_token);
        router.replace("/auth/kyc");
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : "Invalid code", "error");
      setCode("");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    try {
      await api.post("/auth/send-otp", { phone: pendingPhone });
      setResendCountdown(30);
      setCode("");
      toast("New code sent!", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Could not resend", "error");
    }
  }

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      {/* Top section */}
      <div className="bg-hero-pattern px-5 pt-12 pb-14">
        <button
          onClick={() => router.replace("/auth/phone")}
          className="flex items-center gap-1.5 text-sm text-white/70 hover:text-white mb-8"
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </button>

        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/15 border border-white/20 mb-4">
          <MessageSquare className="h-7 w-7 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white">Check your messages</h2>
        <p className="mt-1 text-sm text-white/65">
          Sent to{" "}
          <span className="font-semibold text-white">{formatPhone(pendingPhone)}</span>
        </p>
      </div>

      {/* Code entry */}
      <div className="flex-1 rounded-t-3xl bg-background -mt-4 px-6 pt-8 pb-8 flex flex-col">
        <p className="text-sm font-semibold text-foreground mb-6">Enter 6-digit code</p>

        <div className="flex justify-center">
          <OtpInput
            length={6}
            value={code}
            onChange={setCode}
            disabled={loading}
          />
        </div>

        {loading && (
          <div className="mt-8 flex flex-col items-center gap-2">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <p className="text-sm text-muted-foreground">Verifying…</p>
          </div>
        )}

        <div className="mt-auto pt-8 flex flex-col items-center gap-3">
          {resendCountdown > 0 ? (
            <p className="text-sm text-muted-foreground">
              Resend code in{" "}
              <span className="font-semibold tabular-nums text-foreground">{resendCountdown}s</span>
            </p>
          ) : (
            <Button variant="ghost" size="sm" onClick={handleResend}>
              Resend code
            </Button>
          )}

          <p className="text-xs text-muted-foreground text-center">
            By continuing you agree to our Terms of Service
          </p>
        </div>
      </div>
    </div>
  );
}
