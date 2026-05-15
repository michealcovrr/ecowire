"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { formatNaira } from "@/lib/utils";
import { Bell, Send, Download, Wallet, Briefcase, BarChart2, ShieldCheck, LogOut, ChevronRight, Sparkles, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";

interface WalletBalance {
  balance_kobo: number;
  balance_naira: number;
  account_number: string | null;
  bank_name: string | null;
}

function greet(name: string) {
  const h = new Date().getHours();
  const time = h < 12 ? "Morning" : h < 17 ? "Afternoon" : "Evening";
  return `Good ${time}, ${name}`;
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, squadAccountNumber, squadBankName, logout } = useAuthStore();
  const [balance, setBalance] = useState<number | null>(null);
  const [loadingBalance, setLoadingBalance] = useState(false);

  useEffect(() => {
    async function fetchBalance() {
      setLoadingBalance(true);
      try {
        const res = await api.get<WalletBalance>("/wallet/balance");
        setBalance(res.data.balance_kobo);
      } catch {
        // silent
      } finally {
        setLoadingBalance(false);
      }
    }
    fetchBalance();
  }, []);

  function handleLogout() {
    logout();
    router.replace("/auth/phone");
  }

  const firstName = user?.full_name?.split(" ")[0] ?? "there";
  const kycTier = user?.kyc_tier ?? 1;
  const kycLabel = ["", "Tier 1", "Tier 2 — Verified", "Tier 3 — Full"][kycTier];

  return (
    <div className="flex flex-col pb-6">
      {/* Header */}
      <header className="bg-hero-pattern px-5 pt-12 pb-8">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-white/60 font-medium">{greet(firstName)}</p>
            <h1 className="text-xl font-bold text-white mt-0.5">{user?.full_name ?? "Welcome"}</h1>
            <p className="text-xs text-white/50 font-mono mt-0.5">{user?.user_id}</p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/notifications">
              <button className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors">
                <Bell className="h-4 w-4" />
              </button>
            </Link>
            <button
              onClick={handleLogout}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Balance card — overlaps header */}
      <div className="mx-4 -mt-4 rounded-2xl bg-white shadow-card-lg border border-border/40 p-5">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-xs text-muted-foreground font-medium">Wallet Balance</p>
            {loadingBalance ? (
              <Skeleton className="mt-2 h-9 w-36" />
            ) : (
              <p className="mt-1 text-3xl font-extrabold text-foreground">
                {balance !== null ? formatNaira(balance) : "—"}
              </p>
            )}
          </div>
          <Badge variant={kycTier >= 2 ? "success" : "secondary"}>
            {kycLabel}
          </Badge>
        </div>

        {squadAccountNumber && (
          <div className="rounded-xl bg-accent/50 border border-accent px-3.5 py-2.5 mb-4">
            <p className="text-[10px] uppercase tracking-widest text-primary/60 font-semibold">Fund Account</p>
            <p className="text-sm font-bold text-foreground mt-0.5">{squadAccountNumber}</p>
            {squadBankName && (
              <p className="text-xs text-muted-foreground">{squadBankName}</p>
            )}
          </div>
        )}

        {/* Quick actions */}
        <div className="grid grid-cols-3 gap-2">
          <Link href="/wallet?sheet=send">
            <QuickAction icon={<Send className="h-5 w-5" />} label="Send" />
          </Link>
          <Link href="/wallet?sheet=receive">
            <QuickAction icon={<Download className="h-5 w-5" />} label="Receive" />
          </Link>
          <Link href="/wallet">
            <QuickAction icon={<Wallet className="h-5 w-5" />} label="History" />
          </Link>
        </div>
      </div>

      {/* Feature grid */}
      <div className="mt-5 px-4">
        <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-3">Features</p>
        <div className="grid grid-cols-2 gap-3">
          <FeatureCard
            href="/jobs"
            icon={<Briefcase className="h-7 w-7 text-primary" />}
            bg="bg-accent"
            title="Jobs"
            subtitle="Find work or hire"
          />
          <FeatureCard
            href="/finance"
            icon={<BarChart2 className="h-7 w-7 text-amber-600" />}
            bg="bg-amber-50"
            title="Finance"
            subtitle="Track income & score"
          />
          <FeatureCard
            href="/profile"
            icon={<ShieldCheck className="h-7 w-7 text-primary" />}
            bg="bg-accent"
            title="Work Profile"
            subtitle="Build your skill record"
          />
          <FeatureCard
            href="/community"
            icon={<Users className="h-7 w-7 text-violet-600" />}
            bg="bg-violet-50"
            title="Community"
            subtitle="Your local circle"
          />
        </div>
      </div>

      {/* KYC upgrade prompt */}
      {kycTier === 1 && (
        <div className="mx-4 mt-4 rounded-2xl bg-gold-light border border-gold/30 p-4">
          <div className="flex items-center gap-2 mb-1.5">
            <Sparkles className="h-4 w-4 text-gold-dark" />
            <p className="text-sm font-bold text-gold-foreground">Unlock more with Tier 2</p>
          </div>
          <p className="text-xs text-gold-foreground/70 mb-3">
            Add a government ID to unlock escrow, hiring, and ₦500k/day limits.
          </p>
          <Button
            size="sm"
            className="bg-gold text-gold-foreground hover:bg-gold/90"
            onClick={() => router.push("/profile/kyc-upgrade")}
          >
            Upgrade KYC
          </Button>
        </div>
      )}

      {/* Intent routing prompt (for new users) */}
      {!user?.active_role && (
        <Link href="/intent" className="mx-4 mt-4">
          <div className="rounded-2xl bg-primary p-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/15 flex-shrink-0">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-bold text-white">What are you here to do?</p>
              <p className="text-xs text-white/60">Set your role to get personalised features</p>
            </div>
            <ChevronRight className="h-4 w-4 text-white/50" />
          </div>
        </Link>
      )}

      <div className="h-4" />
    </div>
  );
}

function QuickAction({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex flex-col items-center gap-1.5 rounded-xl bg-muted/50 py-3 hover:bg-accent transition-colors cursor-pointer border border-border/40">
      <div className="text-primary">{icon}</div>
      <span className="text-[11px] font-bold text-foreground/70">{label}</span>
    </div>
  );
}

function FeatureCard({
  href,
  icon,
  bg,
  title,
  subtitle,
}: {
  href: string;
  icon: React.ReactNode;
  bg: string;
  title: string;
  subtitle: string;
}) {
  return (
    <Link
      href={href}
      className="flex flex-col gap-3 rounded-2xl bg-white p-4 shadow-card border border-border/40 hover:shadow-card-md transition-shadow"
    >
      <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${bg}`}>{icon}</div>
      <div>
        <p className="text-sm font-bold text-foreground">{title}</p>
        <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
      </div>
    </Link>
  );
}
