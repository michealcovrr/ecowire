"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { ChevronLeft, ShieldCheck, Lock } from "lucide-react";
import type { AuthSuccessResponse } from "@/lib/types";

export default function KycPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { pendingTempToken, setToken, setUser, setSquadAccount, setQrCode } = useAuthStore();

  const [kycType, setKycType] = useState<"BVN" | "NIN">("NIN");
  const [kycValue, setKycValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [kycError, setKycError] = useState("");

  useEffect(() => {
    if (!pendingTempToken) router.replace("/auth/phone");
  }, [pendingTempToken, router]);

  function handleKycChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value.replace(/\D/g, "").slice(0, 11);
    setKycValue(val);
    if (kycError) setKycError("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (kycValue.length < 4) {
      setKycError(`${kycType} must be at least 4 digits for demo`);
      return;
    }
    setLoading(true);
    try {
      const res = await api.post<AuthSuccessResponse>("/auth/register", {
        temp_token: pendingTempToken,
        kyc_type: kycType,
        kyc_value: kycValue,
      });
      const d = res.data;
      setToken(d.token);
      setUser(d.user);
      setSquadAccount(d.squad_account_number ?? null, d.squad_bank_name ?? null);
      setQrCode(d.qr_code ?? null);
      router.replace("/auth/success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Registration failed", "error");
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
          <ShieldCheck className="h-7 w-7 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white">Verify your identity</h2>
        <p className="mt-1 text-sm text-white/65">
          We use your {kycType} to confirm who you are
        </p>
      </div>

      {/* Form */}
      <div className="flex-1 rounded-t-3xl bg-background -mt-4 px-6 pt-8 pb-8 flex flex-col gap-5">
        {/* Type selector */}
        <div>
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
            Select ID type
          </p>
          <div className="flex gap-3">
            {(["NIN", "BVN"] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => { setKycType(t); setKycValue(""); setKycError(""); }}
                className={`flex-1 rounded-xl border-2 py-3 text-sm font-bold transition-all ${
                  kycType === t
                    ? "border-primary bg-primary text-white shadow-glow"
                    : "border-border text-muted-foreground hover:border-primary/50"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5 flex-1">
          <Input
            label={kycType === "NIN" ? "National Identification Number" : "Bank Verification Number"}
            type="tel"
            inputMode="numeric"
            placeholder="11-digit number"
            value={kycValue}
            onChange={handleKycChange}
            error={kycError}
            hint={kycType === "BVN" ? "Dial *565*0# to get your BVN" : undefined}
          />

          <div className="mt-auto space-y-3">
            <Button
              type="submit"
              className="w-full"
              size="lg"
              loading={loading}
              disabled={kycValue.length < 4}
            >
              {loading ? "Creating your account…" : "Create account"}
            </Button>

            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <Lock className="h-3 w-3" />
              <span>Your data is encrypted and secure</span>
            </div>
          </div>
        </form>

        {/* Trust badge */}
        <div className="rounded-2xl bg-muted/60 border border-border p-4 flex items-start gap-3">
          <ShieldCheck className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-xs font-semibold text-foreground">CBN-compliant KYC</p>
            <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
              We verify using Dojah. Your raw ID number is never stored — only a verified reference.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
