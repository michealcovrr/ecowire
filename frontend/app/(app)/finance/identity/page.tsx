"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { ChevronLeft, RefreshCw, TrendingUp, Star, Sparkles } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/toast";
import { cn } from "@/lib/utils";

interface Identity {
  composite_score: number;
  transaction_score: number;
  job_completion_score: number;
  dispute_score: number;
  repayment_score: number;
  community_trust_score: number;
  engagement_score: number;
  days_on_platform: number;
  eligible_products: string[];
  locked_products: string[];
  improvement_suggestions: string[];
}

const SCORE_ITEMS = [
  { key: "transaction_score", label: "Transactions", color: "bg-blue-500", icon: "💳" },
  { key: "job_completion_score", label: "Job Completion", color: "bg-success", icon: "✅" },
  { key: "dispute_score", label: "Clean Record", color: "bg-emerald-500", icon: "🛡️" },
  { key: "repayment_score", label: "Repayments", color: "bg-violet-500", icon: "🔄" },
  { key: "community_trust_score", label: "Community Trust", color: "bg-gold", icon: "🤝" },
  { key: "engagement_score", label: "Engagement", color: "bg-pink-500", icon: "🔥" },
] as const;

const TIER_LABELS: Record<string, string> = {
  micro_savings: "Micro Savings",
  micro_insurance: "Micro Insurance",
  micro_loan: "Micro Loan",
  working_capital: "Working Capital",
};

export default function IdentityPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    api.get<Identity>("/finance/identity")
      .then((r) => setIdentity(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function refresh() {
    setRefreshing(true);
    try {
      await api.post("/finance/identity/refresh", {});
      const r = await api.get<Identity>("/finance/identity");
      setIdentity(r.data);
      toast("Score refreshed!", "success");
    } catch {
      toast("Could not refresh", "error");
    } finally {
      setRefreshing(false);
    }
  }

  const score = identity?.composite_score ?? 0;
  const scoreLevel = score >= 80 ? "Excellent" : score >= 60 ? "Good" : score >= 40 ? "Building" : "New";
  const scoreColor = score >= 80 ? "text-success" : score >= 60 ? "text-gold-dark" : score >= 40 ? "text-warning" : "text-muted-foreground";

  return (
    <div className="flex flex-col pb-6">
      {/* Header */}
      <div className="bg-hero-pattern px-5 pt-12 pb-10">
        <button onClick={() => router.back()} className="flex items-center gap-1.5 text-sm text-white/70 hover:text-white mb-6">
          <ChevronLeft className="h-4 w-4" /> Back
        </button>

        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-white/50 font-medium">Financial Identity</p>
            <p className="text-4xl font-extrabold text-white mt-1">{Math.round(score)}</p>
            <p className={cn("text-sm font-bold mt-1", scoreColor)}>{scoreLevel}</p>
          </div>

          <button
            onClick={refresh}
            disabled={refreshing}
            className="flex h-10 w-10 items-center justify-center rounded-full bg-white/15 text-white hover:bg-white/25 transition-colors"
          >
            <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
          </button>
        </div>

        {/* Score progress ring (simplified bar) */}
        <div className="mt-4 h-2 bg-white/20 rounded-full overflow-hidden">
          <div
            className="h-full bg-gold rounded-full transition-all duration-1000"
            style={{ width: `${Math.min(score, 100)}%` }}
          />
        </div>
      </div>

      <div className="px-4 mt-5 space-y-4">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16" />)}
          </div>
        ) : identity ? (
          <>
            {/* Score breakdown */}
            <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4 space-y-4">
              <div className="flex items-center gap-2 mb-1">
                <Star className="h-4 w-4 text-gold" />
                <p className="text-sm font-bold text-foreground">Score Breakdown</p>
              </div>
              {SCORE_ITEMS.map(({ key, label, color, icon }) => {
                const value = identity[key];
                return (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-muted-foreground font-medium">{icon} {label}</span>
                      <span className="font-bold text-foreground">{Math.round(value)}%</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${color}`}
                        style={{ width: `${value}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4 text-center">
                <p className="text-2xl font-extrabold text-foreground">{identity.days_on_platform}</p>
                <p className="text-xs text-muted-foreground mt-0.5">Days on platform</p>
              </div>
              <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4 text-center">
                <p className="text-2xl font-extrabold text-primary">{identity.eligible_products.length}</p>
                <p className="text-xs text-muted-foreground mt-0.5">Products unlocked</p>
              </div>
            </div>

            {/* Eligible products */}
            {identity.eligible_products.length > 0 && (
              <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="h-4 w-4 text-gold" />
                  <p className="text-sm font-bold text-foreground">Unlocked Products</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {identity.eligible_products.map((p) => (
                    <Badge key={p} variant="success">
                      {TIER_LABELS[p] ?? p.replace(/_/g, " ")}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Improvement tips */}
            {identity.improvement_suggestions?.length > 0 && (
              <div className="rounded-2xl bg-accent/40 border border-accent p-4">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="h-4 w-4 text-primary" />
                  <p className="text-sm font-bold text-primary">How to improve your score</p>
                </div>
                <div className="space-y-2">
                  {identity.improvement_suggestions.map((s, i) => (
                    <p key={i} className="text-xs text-primary/70 leading-relaxed">
                      {i + 1}. {s}
                    </p>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
