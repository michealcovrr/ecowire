"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { api } from "@/lib/api";
import { formatNaira } from "@/lib/utils";
import { ArrowUpRight, ArrowDownLeft, Copy, Send, Download, RefreshCw, Wallet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Drawer } from "@/components/ui/drawer";
import { useToast } from "@/components/ui/toast";

interface Balance {
  balance_kobo: number;
  balance_naira: number;
  account_number: string | null;
  bank_name: string | null;
}

interface LocalTxn {
  transaction_id: string;
  type: string;
  amount_kobo: number;
  amount_naira: number;
  status: string;
  tagged_as: string | null;
  timestamp: string | null;
}

type Sheet = "send" | "receive" | null;

export default function WalletPage() {
  const { squadAccountNumber, squadBankName, user } = useAuthStore();
  const { toast } = useToast();
  const searchParams = useSearchParams();

  const [balance, setBalance] = useState<Balance | null>(null);
  const [txns, setTxns] = useState<LocalTxn[]>([]);
  const [loading, setLoading] = useState(true);
  const [sheet, setSheet] = useState<Sheet>(null);

  useEffect(() => {
    const s = searchParams.get("sheet");
    if (s === "send" || s === "receive") setSheet(s);
  }, [searchParams]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [balRes, txRes] = await Promise.all([
        api.get<Balance>("/wallet/balance"),
        api.get<{ local_transactions: LocalTxn[] }>("/wallet/transactions"),
      ]);
      setBalance(balRes.data);
      setTxns(txRes.data.local_transactions ?? []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  function copyAccount() {
    if (!squadAccountNumber) return;
    navigator.clipboard.writeText(squadAccountNumber).then(() => toast("Account number copied!", "success"));
  }

  return (
    <div className="flex flex-col pb-6">
      {/* Header */}
      <div className="bg-hero-pattern px-5 pt-12 pb-16">
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm text-white/60 font-medium">Wallet Balance</p>
          <button onClick={fetchData} className="text-white/50 hover:text-white transition-colors">
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
        {loading ? (
          <div className="h-10 w-44 rounded-xl bg-white/20 animate-pulse" />
        ) : (
          <p className="text-4xl font-extrabold text-white">
            {balance ? formatNaira(balance.balance_kobo) : "₦0.00"}
          </p>
        )}
      </div>

      {/* Account card — overlaps header */}
      <div className="mx-4 -mt-8 rounded-2xl bg-white shadow-card-lg border border-border/40 p-4">
        <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">
          Fund this account to add money
        </p>
        <div className="flex items-center justify-between mt-1.5">
          <div>
            <p className="text-lg font-extrabold text-foreground">{squadAccountNumber ?? "—"}</p>
            {squadBankName && <p className="text-xs text-muted-foreground">{squadBankName}</p>}
          </div>
          <button
            onClick={copyAccount}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-primary hover:bg-primary hover:text-white transition-colors"
          >
            <Copy className="h-4 w-4" />
          </button>
        </div>

        {/* Action buttons */}
        <div className="mt-4 grid grid-cols-2 gap-2">
          <Button className="w-full gap-2" size="sm" onClick={() => setSheet("send")}>
            <Send className="h-4 w-4" /> Send Money
          </Button>
          <Button variant="outline" className="w-full gap-2" size="sm" onClick={() => setSheet("receive")}>
            <Download className="h-4 w-4" /> Receive
          </Button>
        </div>
      </div>

      {/* Transactions */}
      <div className="mt-5 px-4">
        <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-3">
          Transactions
        </h2>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16" />)}
          </div>
        ) : txns.length === 0 ? (
          <div className="rounded-2xl bg-white border border-border/40 p-8 text-center shadow-card">
            <Wallet className="h-10 w-10 text-muted mx-auto mb-3" />
            <p className="text-sm text-muted-foreground font-medium">No transactions yet.</p>
            <p className="text-xs text-muted-foreground mt-1">Fund your account to get started.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {txns.map((t) => (
              <TxnRow key={t.transaction_id} txn={t} />
            ))}
          </div>
        )}
      </div>

      {/* Send Drawer */}
      <Drawer
        open={sheet === "send"}
        onOpenChange={(o) => { if (!o) { setSheet(null); fetchData(); } }}
        title="Send Money"
      >
        <SendForm onDone={() => { setSheet(null); fetchData(); }} />
      </Drawer>

      {/* Receive Drawer */}
      <Drawer
        open={sheet === "receive"}
        onOpenChange={(o) => { if (!o) setSheet(null); }}
        title="Receive Money"
      >
        <ReceiveContent
          accountNumber={squadAccountNumber}
          bankName={squadBankName}
          userId={user?.user_id}
        />
      </Drawer>
    </div>
  );
}

function TxnRow({ txn }: { txn: LocalTxn }) {
  const isSend = txn.type === "send" || txn.type === "cash_out";
  const label = ({
    send: "Sent",
    receive: "Received",
    cash_in: "Cash In",
    cash_out: "Cash Out",
    escrow: "Escrow Hold",
    release: "Released",
    loan: "Loan",
    repayment: "Repayment",
  } as Record<string, string>)[txn.type] ?? txn.type;

  return (
    <div className="flex items-center justify-between rounded-2xl bg-white border border-border/40 shadow-card px-4 py-3">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${isSend ? "bg-destructive-light" : "bg-accent"}`}>
          {isSend
            ? <ArrowUpRight className="h-5 w-5 text-destructive" />
            : <ArrowDownLeft className="h-5 w-5 text-primary" />}
        </div>
        <div>
          <p className="text-sm font-bold text-foreground">{label}</p>
          <p className="text-xs text-muted-foreground">
            {txn.timestamp ? new Date(txn.timestamp).toLocaleDateString("en-NG", { day: "numeric", month: "short" }) : "—"}
          </p>
        </div>
      </div>
      <div className="text-right">
        <p className={`text-sm font-extrabold ${isSend ? "text-destructive" : "text-primary"}`}>
          {isSend ? "-" : "+"}{formatNaira(txn.amount_kobo)}
        </p>
        <p className={`text-[10px] font-medium ${txn.status === "completed" ? "text-muted-foreground" : "text-warning"}`}>
          {txn.status}
        </p>
      </div>
    </div>
  );
}

function SendForm({ onDone }: { onDone: () => void }) {
  const { toast } = useToast();
  const [recipientId, setRecipientId] = useState("");
  const [amountNaira, setAmountNaira] = useState("");
  const [narration, setNarration] = useState("");
  const [loading, setLoading] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  async function handleSend() {
    if (!recipientId.trim() || !amountNaira) return;
    const kobo = Math.round(parseFloat(amountNaira) * 100);
    if (kobo < 100) { toast("Minimum send is ₦1", "error"); return; }
    setLoading(true);
    try {
      await api.post("/wallet/send", {
        recipient_id: recipientId.trim().toUpperCase(),
        amount_kobo: kobo,
        amount_naira: parseFloat(amountNaira),
        narration: narration || "alwi transfer",
      });
      toast(`₦${amountNaira} sent!`, "success");
      setConfirmed(true);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Transfer failed", "error");
    } finally {
      setLoading(false);
    }
  }

  if (confirmed) {
    return (
      <div className="flex flex-col items-center py-8">
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-accent mb-4">
          <ArrowUpRight className="h-10 w-10 text-primary" />
        </div>
        <p className="text-2xl font-extrabold text-foreground">Sent!</p>
        <p className="text-sm text-muted-foreground mt-1">₦{amountNaira} to {recipientId.toUpperCase()}</p>
        <Button className="mt-8 w-full" size="lg" onClick={onDone}>Done</Button>
      </div>
    );
  }

  return (
    <div className="space-y-4 pb-2">
      <Input
        label="Recipient ECO ID"
        placeholder="ECO-XXXX-XXXX"
        value={recipientId}
        onChange={(e) => setRecipientId(e.target.value)}
      />
      <Input
        label="Amount (₦)"
        type="number"
        inputMode="decimal"
        placeholder="0.00"
        value={amountNaira}
        onChange={(e) => setAmountNaira(e.target.value)}
      />
      <Input
        label="Description (optional)"
        placeholder="What's this for?"
        value={narration}
        onChange={(e) => setNarration(e.target.value)}
      />
      <Button
        className="w-full"
        size="lg"
        onClick={handleSend}
        loading={loading}
        disabled={!recipientId || !amountNaira || loading}
      >
        Send Money
      </Button>
    </div>
  );
}

function ReceiveContent({
  accountNumber,
  bankName,
  userId,
}: {
  accountNumber: string | null;
  bankName: string | null;
  userId?: string;
}) {
  const { toast } = useToast();

  function copy(text: string, label: string) {
    navigator.clipboard.writeText(text).then(() => toast(`${label} copied!`, "success"));
  }

  return (
    <div className="space-y-3 pb-2">
      {accountNumber && (
        <button
          onClick={() => copy(accountNumber, "Account number")}
          className="w-full flex items-center justify-between rounded-2xl bg-accent border border-accent-foreground/10 p-4 text-left hover:bg-accent/80 transition-colors"
        >
          <div>
            <p className="text-[10px] uppercase tracking-widest text-primary/60 font-semibold">Bank Transfer</p>
            <p className="text-xl font-extrabold text-foreground mt-0.5">{accountNumber}</p>
            {bankName && <p className="text-xs text-muted-foreground">{bankName}</p>}
          </div>
          <Copy className="h-5 w-5 text-primary flex-shrink-0" />
        </button>
      )}
      {userId && (
        <button
          onClick={() => copy(userId, "ECO ID")}
          className="w-full flex items-center justify-between rounded-2xl bg-muted/50 border border-border p-4 text-left hover:bg-muted transition-colors"
        >
          <div>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">ECO ID (app transfer)</p>
            <p className="text-lg font-extrabold font-mono text-foreground mt-0.5">{userId}</p>
          </div>
          <Copy className="h-5 w-5 text-muted-foreground flex-shrink-0" />
        </button>
      )}
      <p className="text-xs text-muted-foreground text-center pt-2">
        Share your account number or ECO ID to receive payments
      </p>
    </div>
  );
}
