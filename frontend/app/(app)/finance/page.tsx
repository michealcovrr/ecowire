"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  TrendingUp, TrendingDown, RefreshCw, Lock, Unlock,
  ChevronRight, AlertCircle, CheckCircle2,
  PiggyBank, Shield, Banknote, Briefcase, X, Plus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";

function fmt(n: number) {
  return new Intl.NumberFormat("en-NG", {
    style: "currency", currency: "NGN",
    minimumFractionDigits: 0, maximumFractionDigits: 0,
  }).format(n);
}

interface Summary {
  period: string;
  total_income_naira: number;
  total_expense_naira: number;
  net_naira: number;
  by_category: Record<string, { income_naira: number; expense_naira: number }>;
}

interface LogEntry {
  log_id: string;
  entry_type: "income" | "expense" | "debt_owed" | "debt_owing";
  amount_naira: number;
  category: string;
  description: string;
  source: string;
  timestamp: string;
}

interface Logs {
  totals: { income_naira: number; expense_naira: number; net_naira: number };
  logs: LogEntry[];
}

interface ProductProgress {
  score: number;
  days: number;
  disputes_ok?: boolean;
  kyc_tier?: number;
  business_role?: boolean;
}

interface Product {
  key: string;
  name: string;
  description: string;
  unlocked: boolean;
  progress: ProductProgress;
  requirements: string;
  max_amount_naira?: number;
  interest_rate_pct?: number;
}

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
  products?: Product[];
}

interface Debt {
  debt_id: string;
  debtor_name: string;
  amount_naira: number;
  reason: string;
  status: "outstanding" | "settled";
  created_at: string;
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-muted-foreground font-medium">{label}</span>
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
}

const TABS = ["Overview", "Log", "Products", "Debts"] as const;
type Tab = typeof TABS[number];

export default function FinancePage() {
  const { toast } = useToast();
  const [tab, setTab] = useState<Tab>("Overview");

  const [summary, setSummary] = useState<Summary | null>(null);
  const [logs, setLogs] = useState<Logs | null>(null);
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [debts, setDebts] = useState<Debt[]>([]);
  const [debtOutstanding, setDebtOutstanding] = useState(0);

  const [logText, setLogText] = useState("");
  const [logSaving, setLogSaving] = useState(false);

  const [showDebtForm, setShowDebtForm] = useState(false);
  const [debtName, setDebtName] = useState("");
  const [debtAmount, setDebtAmount] = useState("");
  const [debtReason, setDebtReason] = useState("");
  const [debtSaving, setDebtSaving] = useState(false);

  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [loadingIdentity, setLoadingIdentity] = useState(false);
  const [loadingDebts, setLoadingDebts] = useState(false);

  const fetchSummary = useCallback(async () => {
    setLoadingSummary(true);
    try {
      const r = await api.get<Summary>("/finance/summary?period=monthly");
      setSummary(r.data);
    } catch {} finally { setLoadingSummary(false); }
  }, []);

  const fetchLogs = useCallback(async () => {
    setLoadingLogs(true);
    try {
      const r = await api.get<Logs>("/finance/logs?limit=30");
      setLogs(r.data);
    } catch {} finally { setLoadingLogs(false); }
  }, []);

  const fetchIdentity = useCallback(async () => {
    setLoadingIdentity(true);
    try {
      const [idRes, prodRes] = await Promise.all([
        api.get<Identity>("/finance/identity"),
        api.get<{ composite_score: number; products: Product[] }>("/finance/products"),
      ]);
      setIdentity(idRes.data);
      setProducts(prodRes.data.products);
    } catch {} finally { setLoadingIdentity(false); }
  }, []);

  const fetchDebts = useCallback(async () => {
    setLoadingDebts(true);
    try {
      const r = await api.get<{ outstanding_total_naira: number; debts: Debt[] }>("/finance/debts");
      setDebts(r.data.debts);
      setDebtOutstanding(r.data.outstanding_total_naira);
    } catch {} finally { setLoadingDebts(false); }
  }, []);

  useEffect(() => {
    if (tab === "Overview") fetchSummary();
    else if (tab === "Log") fetchLogs();
    else if (tab === "Products") fetchIdentity();
    else if (tab === "Debts") fetchDebts();
  }, [tab, fetchSummary, fetchLogs, fetchIdentity, fetchDebts]);

  async function submitLog(e: React.FormEvent) {
    e.preventDefault();
    if (!logText.trim()) return;
    setLogSaving(true);
    try {
      const r = await api.post<{ entry_type: string; amount_naira: number; category: string }>(
        "/finance/log", { text: logText }
      );
      toast(`Logged: ${r.data.entry_type} — ${fmt(r.data.amount_naira)} (${r.data.category})`, "success");
      setLogText("");
      fetchLogs();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to log", "error");
    } finally { setLogSaving(false); }
  }

  async function submitDebt(e: React.FormEvent) {
    e.preventDefault();
    if (!debtName || !debtAmount || !debtReason) return;
    setDebtSaving(true);
    try {
      await api.post("/finance/debt", {
        debtor_name: debtName,
        amount_kobo: Math.round(parseFloat(debtAmount) * 100),
        reason: debtReason,
      });
      toast("Debt recorded!", "success");
      setDebtName(""); setDebtAmount(""); setDebtReason("");
      setShowDebtForm(false);
      fetchDebts();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed", "error");
    } finally { setDebtSaving(false); }
  }

  async function settleDebt(debtId: string) {
    try {
      await api.patch(`/finance/debt/${debtId}/settle`);
      toast("Marked as settled!", "success");
      fetchDebts();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed", "error");
    }
  }

  async function refreshIdentity() {
    setLoadingIdentity(true);
    try {
      await api.post("/finance/identity/refresh", {});
      await fetchIdentity();
      toast("Score refreshed!", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed", "error");
    } finally { setLoadingIdentity(false); }
  }

  function handleProductAction(key: string) {
    toast(`${key.replace(/_/g, " ")} — apply flow coming soon`, "info");
  }

  return (
    <div className="flex flex-col min-h-dvh pb-24">
      {/* Header */}
      <div className="bg-primary px-5 pt-12 pb-5">
        <h1 className="text-xl font-extrabold text-white">Finance</h1>
        <p className="text-sm text-white/60 mt-0.5">Track money, build your financial identity</p>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-border/60 flex overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "flex-shrink-0 px-4 py-3 text-xs font-bold border-b-2 transition-colors",
              tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground"
            )}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="px-4 pt-4 space-y-3">
        {/* ── OVERVIEW ─────────────────────────────────────────────────────── */}
        {tab === "Overview" && (
          <>
            {loadingSummary && !summary
              ? [1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)
              : summary ? (
                <>
                  <div className={cn(
                    "rounded-2xl p-4 shadow-card-md",
                    summary.net_naira >= 0 ? "bg-primary" : "bg-destructive"
                  )}>
                    <p className="text-xs text-white/60 font-medium">{summary.period} · Net</p>
                    <p className="text-3xl font-extrabold text-white mt-0.5">
                      {summary.net_naira >= 0 ? "+" : ""}{fmt(summary.net_naira)}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4">
                      <div className="flex items-center gap-1.5 mb-1">
                        <TrendingUp className="h-4 w-4 text-success" />
                        <p className="text-xs text-muted-foreground font-medium">Income</p>
                      </div>
                      <p className="text-base font-extrabold text-foreground">{fmt(summary.total_income_naira)}</p>
                    </div>
                    <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4">
                      <div className="flex items-center gap-1.5 mb-1">
                        <TrendingDown className="h-4 w-4 text-destructive" />
                        <p className="text-xs text-muted-foreground font-medium">Expenses</p>
                      </div>
                      <p className="text-base font-extrabold text-foreground">{fmt(summary.total_expense_naira)}</p>
                    </div>
                  </div>

                  {Object.keys(summary.by_category).length > 0 && (
                    <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4">
                      <p className="text-xs font-bold text-foreground mb-3">By Category</p>
                      <div className="space-y-3">
                        {Object.entries(summary.by_category).map(([cat, vals]) => (
                          <div key={cat}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="capitalize text-muted-foreground font-medium">{cat}</span>
                              <span className="text-muted-foreground">
                                {vals.income_naira > 0 && (
                                  <span className="text-success font-bold mr-2">+{fmt(vals.income_naira)}</span>
                                )}
                                {vals.expense_naira > 0 && (
                                  <span className="text-destructive font-bold">-{fmt(vals.expense_naira)}</span>
                                )}
                              </span>
                            </div>
                            <div className="h-2 bg-muted rounded-full overflow-hidden flex">
                              {vals.income_naira > 0 && (
                                <div className="h-full bg-success rounded-full"
                                  style={{ width: `${(vals.income_naira / (vals.income_naira + vals.expense_naira || 1)) * 100}%` }} />
                              )}
                              {vals.expense_naira > 0 && (
                                <div className="h-full bg-destructive/50 rounded-full"
                                  style={{ width: `${(vals.expense_naira / (vals.income_naira + vals.expense_naira || 1)) * 100}%` }} />
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <button onClick={fetchSummary} className="w-full text-xs text-primary py-2 font-bold">
                    Refresh
                  </button>
                </>
              ) : null}
          </>
        )}

        {/* ── LOG ──────────────────────────────────────────────────────────── */}
        {tab === "Log" && (
          <>
            {logs && (
              <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4 flex gap-3">
                {[
                  { label: "Income", value: fmt(logs.totals.income_naira), color: "text-success" },
                  { label: "Expense", value: fmt(logs.totals.expense_naira), color: "text-destructive" },
                  { label: "Net", value: fmt(logs.totals.net_naira), color: logs.totals.net_naira >= 0 ? "text-foreground" : "text-destructive" },
                ].map((item, i) => (
                  <div key={i} className={cn("flex-1 text-center", i > 0 && "border-l border-border/60")}>
                    <p className="text-[10px] text-muted-foreground font-medium">{item.label}</p>
                    <p className={cn("text-xs font-extrabold mt-0.5", item.color)}>{item.value}</p>
                  </div>
                ))}
              </div>
            )}

            <form onSubmit={submitLog} className="rounded-2xl bg-accent/40 border border-accent p-4 space-y-3">
              <p className="text-xs font-bold text-primary">Log an Entry (AI-powered)</p>
              <textarea
                className="w-full rounded-xl border-2 border-border bg-white px-3 py-2.5 text-sm focus:outline-none focus:border-primary resize-none text-foreground placeholder:text-muted-foreground/60"
                rows={2}
                placeholder='"I sold 5 bags of cement for ₦30,000" or "Paid ₦2,500 for transport"'
                value={logText}
                onChange={(e) => setLogText(e.target.value)}
              />
              <Button size="sm" className="w-full" loading={logSaving} disabled={!logText.trim()}>
                Log with AI
              </Button>
            </form>

            {loadingLogs && !logs
              ? [1, 2, 3].map((i) => <Skeleton key={i} className="h-14" />)
              : logs?.logs.length ? (
                <div className="space-y-2">
                  {logs.logs.map((entry) => (
                    <div key={entry.log_id} className="flex items-center gap-3 rounded-2xl bg-white border border-border/40 shadow-card p-3">
                      <div className={cn(
                        "flex h-9 w-9 items-center justify-center rounded-xl flex-shrink-0",
                        entry.entry_type === "income" ? "bg-success-light" : "bg-destructive-light"
                      )}>
                        {entry.entry_type === "income"
                          ? <TrendingUp className="h-4 w-4 text-success" />
                          : <TrendingDown className="h-4 w-4 text-destructive" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-bold text-foreground truncate">{entry.description}</p>
                        <p className="text-[10px] text-muted-foreground capitalize">{entry.category} · {entry.source}</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className={cn("text-sm font-extrabold", entry.entry_type === "income" ? "text-success" : "text-destructive")}>
                          {entry.entry_type === "income" ? "+" : "-"}{fmt(entry.amount_naira)}
                        </p>
                        <p className="text-[10px] text-muted-foreground">
                          {new Date(entry.timestamp).toLocaleDateString("en-NG", { day: "numeric", month: "short" })}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : logs ? (
                <div className="rounded-2xl bg-white border border-border/40 shadow-card p-6 text-center">
                  <p className="text-sm text-muted-foreground">No entries yet. Log one above.</p>
                </div>
              ) : null}
          </>
        )}

        {/* ── PRODUCTS ─────────────────────────────────────────────────────── */}
        {tab === "Products" && (
          <>
            {loadingIdentity && !identity
              ? [1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)
              : identity ? (
                <>
                  <div className="rounded-2xl bg-white border border-border/40 shadow-card p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <p className="text-sm font-bold text-foreground">Financial Identity</p>
                        <p className="text-xs text-muted-foreground">{identity.days_on_platform} days on platform</p>
                      </div>
                      <button onClick={refreshIdentity} className="p-2 rounded-xl bg-muted text-muted-foreground hover:bg-accent hover:text-primary transition-colors">
                        <RefreshCw className={cn("h-4 w-4", loadingIdentity && "animate-spin")} />
                      </button>
                    </div>
                    <div className="space-y-3">
                      <ScoreBar label="Transactions & Logs" value={identity.transaction_score} color="bg-blue-500" />
                      <ScoreBar label="Job Completion" value={identity.job_completion_score} color="bg-success" />
                      <ScoreBar label="Dispute Record" value={identity.dispute_score} color="bg-emerald-500" />
                      <ScoreBar label="Repayment History" value={identity.repayment_score} color="bg-violet-500" />
                      <ScoreBar label="Community Trust" value={identity.community_trust_score} color="bg-gold" />
                      <ScoreBar label="Platform Engagement" value={identity.engagement_score} color="bg-pink-500" />
                    </div>
                    {identity.improvement_suggestions?.length > 0 && (
                      <div className="mt-4 rounded-xl bg-accent/50 border border-accent p-3">
                        <p className="text-[10px] font-bold text-primary mb-1.5">How to improve</p>
                        {identity.improvement_suggestions.slice(0, 3).map((s, i) => (
                          <p key={i} className="text-[11px] text-primary/70 leading-relaxed">· {s}</p>
                        ))}
                      </div>
                    )}
                  </div>

                  {products.map((p) => <ProductCard key={p.key} product={p} onAction={handleProductAction} />)}
                </>
              ) : null}
          </>
        )}

        {/* ── DEBTS ────────────────────────────────────────────────────────── */}
        {tab === "Debts" && (
          <>
            <div className="rounded-2xl bg-warning p-4 shadow-card-md">
              <p className="text-xs text-white/70 font-medium">Outstanding Owed to You</p>
              <p className="text-3xl font-extrabold text-white mt-0.5">{fmt(debtOutstanding)}</p>
            </div>

            <button
              onClick={() => setShowDebtForm(!showDebtForm)}
              className="flex items-center gap-2 text-xs font-bold text-primary"
            >
              {showDebtForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
              {showDebtForm ? "Cancel" : "Record a Debt"}
            </button>

            {showDebtForm && (
              <form onSubmit={submitDebt} className="rounded-2xl bg-accent/40 border border-accent p-4 space-y-3">
                <Input label="Debtor name" placeholder="Who owes you?" value={debtName}
                  onChange={(e) => setDebtName(e.target.value)} />
                <Input label="Amount (₦)" type="number" placeholder="e.g. 5000" value={debtAmount}
                  onChange={(e) => setDebtAmount(e.target.value)} />
                <Input label="Reason" placeholder="What for?" value={debtReason}
                  onChange={(e) => setDebtReason(e.target.value)} />
                <Button size="sm" className="w-full" loading={debtSaving}
                  disabled={!debtName || !debtAmount || !debtReason}>
                  Record Debt
                </Button>
              </form>
            )}

            {loadingDebts && debts.length === 0
              ? [1, 2].map((i) => <Skeleton key={i} className="h-16" />)
              : debts.length > 0 ? (
                <div className="space-y-2">
                  {debts.map((debt) => (
                    <div key={debt.debt_id} className={cn(
                      "flex items-center gap-3 rounded-2xl p-4 border shadow-card",
                      debt.status === "settled" ? "bg-muted/40 border-border/40 opacity-60" : "bg-white border-border/40"
                    )}>
                      <div className={cn(
                        "flex h-9 w-9 items-center justify-center rounded-xl flex-shrink-0",
                        debt.status === "settled" ? "bg-success-light" : "bg-warning-light"
                      )}>
                        {debt.status === "settled"
                          ? <CheckCircle2 className="h-4 w-4 text-success" />
                          : <AlertCircle className="h-4 w-4 text-warning" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-foreground">{debt.debtor_name}</p>
                        <p className="text-xs text-muted-foreground truncate">{debt.reason}</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p className="text-sm font-extrabold text-warning">{fmt(debt.amount_naira)}</p>
                        {debt.status === "outstanding" && (
                          <button onClick={() => settleDebt(debt.debt_id)} className="text-[10px] text-primary font-bold">
                            Mark settled
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-2xl bg-white border border-border/40 shadow-card p-6 text-center">
                  <p className="text-sm text-muted-foreground">No debts recorded.</p>
                </div>
              )}
          </>
        )}
      </div>
    </div>
  );
}

function ProductCard({ product, onAction }: { product: Product; onAction: (key: string) => void }) {
  const icons: Record<string, React.ReactNode> = {
    micro_savings: <PiggyBank className="h-5 w-5" />,
    micro_insurance: <Shield className="h-5 w-5" />,
    micro_loan: <Banknote className="h-5 w-5" />,
    working_capital: <Briefcase className="h-5 w-5" />,
  };

  const minProg = Math.min(
    product.progress.score ?? 100,
    product.progress.days ?? 100,
    product.progress.kyc_tier ?? 100,
  );

  return (
    <div className={cn(
      "rounded-2xl p-4 border shadow-card",
      product.unlocked ? "bg-white border-success/30" : "bg-muted/30 border-border/40"
    )}>
      <div className="flex items-start gap-3">
        <div className={cn(
          "flex h-10 w-10 items-center justify-center rounded-xl flex-shrink-0",
          product.unlocked ? "bg-success-light text-success" : "bg-muted text-muted-foreground"
        )}>
          {icons[product.key] ?? <Banknote className="h-5 w-5" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-bold text-foreground">{product.name}</p>
            {product.unlocked
              ? <Unlock className="h-3.5 w-3.5 text-success" />
              : <Lock className="h-3.5 w-3.5 text-muted-foreground" />}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">{product.description}</p>

          {!product.unlocked && (
            <div className="mt-2">
              <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary/40 rounded-full transition-all" style={{ width: `${minProg}%` }} />
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">{product.requirements}</p>
            </div>
          )}

          {product.unlocked && product.key === "micro_loan" && product.max_amount_naira && (
            <p className="text-xs text-success font-bold mt-1">
              Up to {fmt(product.max_amount_naira)} at {product.interest_rate_pct}%/mo
            </p>
          )}
        </div>
        {product.unlocked && (
          <button
            onClick={() => onAction(product.key)}
            className="flex-shrink-0 flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white hover:bg-primary/90 transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
