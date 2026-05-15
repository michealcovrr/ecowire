"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth";
import { CheckCircle2, Copy, Wallet, Sparkles } from "lucide-react";
import { useToast } from "@/components/ui/toast";

export default function SuccessPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { user, squadAccountNumber, squadBankName, token } = useAuthStore();

  useEffect(() => {
    if (!token) router.replace("/auth/phone");
  }, [token, router]);

  function copyId() {
    if (!user?.user_id) return;
    navigator.clipboard.writeText(user.user_id).then(() => toast("ECO ID copied!", "success"));
  }

  function copyAccount() {
    if (!squadAccountNumber) return;
    navigator.clipboard.writeText(squadAccountNumber).then(() => toast("Account number copied!", "success"));
  }

  const firstName = user?.full_name?.split(" ")[0] ?? "there";

  return (
    <div className="flex min-h-dvh flex-col bg-background">
      {/* Hero */}
      <div className="bg-hero-pattern flex flex-col items-center px-6 pt-16 pb-14">
        <div className="mb-5 flex h-24 w-24 items-center justify-center rounded-full bg-white/15 border border-white/25 shadow-glass">
          <CheckCircle2 className="h-14 w-14 text-white" strokeWidth={1.5} />
        </div>
        <h2 className="text-3xl font-extrabold text-white text-center">
          You&apos;re in, {firstName}!
        </h2>
        <p className="mt-2 text-center text-sm text-white/65 max-w-[220px]">
          Your EcoNet account is active. Your financial identity starts now.
        </p>
      </div>

      {/* Cards */}
      <div className="flex-1 rounded-t-3xl bg-background -mt-4 px-5 pt-7 pb-8 space-y-4">
        {/* ECO ID card */}
        <div className="rounded-2xl bg-primary p-5 relative overflow-hidden shadow-card-lg">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-4 w-4 text-gold" />
            <p className="text-xs font-semibold uppercase tracking-widest text-white/60">
              Your ECO ID
            </p>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-extrabold tracking-wider text-white font-mono">
              {user?.user_id ?? "—"}
            </span>
            <button
              onClick={copyId}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/15 text-white hover:bg-white/25 transition-colors"
            >
              <Copy className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-2 text-xs text-white/50">
            Share this ID to receive payments or be found for jobs
          </p>
        </div>

        {/* Wallet account */}
        {squadAccountNumber && (
          <div className="rounded-2xl bg-white border border-border/60 shadow-card p-5">
            <div className="flex items-center gap-2 mb-3">
              <Wallet className="h-4 w-4 text-muted-foreground" />
              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
                Wallet Account
              </p>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xl font-bold text-foreground">{squadAccountNumber}</p>
                {squadBankName && (
                  <p className="text-sm text-muted-foreground mt-0.5">{squadBankName}</p>
                )}
              </div>
              <button
                onClick={copyAccount}
                className="flex h-9 w-9 items-center justify-center rounded-xl bg-muted text-muted-foreground hover:bg-primary hover:text-white transition-colors"
              >
                <Copy className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Transfer money to this account to fund your wallet
            </p>
          </div>
        )}

        {/* KYC Tier */}
        <div className="rounded-2xl bg-accent border border-accent-foreground/10 p-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 flex-shrink-0">
            <CheckCircle2 className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold text-primary">Tier 1 — Verified</p>
            <p className="text-xs text-primary/70 mt-0.5">
              ₦50k/day limit · Add a gov ID to unlock escrow & hiring
            </p>
          </div>
        </div>

        <div className="pt-2">
          <Button
            className="w-full"
            size="lg"
            onClick={() => router.replace("/dashboard")}
          >
            Enter EcoNet →
          </Button>
        </div>
      </div>
    </div>
  );
}
