"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { formatNaira } from "@/lib/utils";
import { ChevronLeft, Send, Lock, Wallet, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { cn } from "@/lib/utils";

interface Message {
  message_id: string;
  sender_user_id: string;
  content: string;
  message_type: string;
  timestamp: string;
  is_mine: boolean;
}

interface Agreement {
  agreed_price_kobo: number | null;
  agreed_price_naira: number | null;
  job_scope: string | null;
  timeline: string | null;
  confirmed_by_employer: boolean;
  confirmed_by_worker: boolean;
  locked: boolean;
}

interface Escrow {
  escrow_id: string;
  status: string;
  amount_kobo: number;
  amount_naira: number;
  account_number: string;
}

interface ChatDetail {
  chat_id: string;
  job_id: string;
  job_status: string;
  job_description: string;
  employer_user_id: string;
  worker_user_id: string;
  role: "employer" | "worker";
  messages: Message[];
  agreement: Agreement | null;
}

export default function ChatPage() {
  const { chatId } = useParams<{ chatId: string }>();
  const router = useRouter();
  const { toast } = useToast();
  useAuthStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  const [chat, setChat] = useState<ChatDetail | null>(null);
  const [escrow, setEscrow] = useState<Escrow | null>(null);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showAgreement, setShowAgreement] = useState(false);

  const [agrPrice, setAgrPrice] = useState("");
  const [agrScope, setAgrScope] = useState("");
  const [agrTimeline, setAgrTimeline] = useState("");
  const [agrSaving, setAgrSaving] = useState(false);

  const fetchChat = useCallback(async () => {
    try {
      const res = await api.get<ChatDetail>(`/chat/${chatId}/messages`);
      setChat(res.data);
      if (res.data.agreement && !res.data.agreement.locked) {
        setAgrPrice(String((res.data.agreement.agreed_price_kobo ?? 0) / 100));
        setAgrScope(res.data.agreement.job_scope ?? "");
        setAgrTimeline(res.data.agreement.timeline ?? "");
      }
    } catch {}
  }, [chatId]);

  const fetchEscrow = useCallback(async () => {
    try {
      const res = await api.get<{ escrow: Escrow | null }>(`/chat/${chatId}/escrow`);
      setEscrow(res.data.escrow);
    } catch {}
  }, [chatId]);

  useEffect(() => {
    Promise.all([fetchChat(), fetchEscrow()]).finally(() => setLoading(false));
    const poll = setInterval(() => { fetchChat(); fetchEscrow(); }, 4000);
    return () => clearInterval(poll);
  }, [fetchChat, fetchEscrow]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat?.messages.length]);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim() || sending) return;
    setSending(true);
    const content = text.trim();
    setText("");
    try {
      await api.post(`/chat/${chatId}/messages`, { content });
      fetchChat();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to send", "error");
      setText(content);
    } finally {
      setSending(false);
    }
  }

  async function proposeAgreement() {
    if (!agrPrice || !agrScope || !agrTimeline) return;
    setAgrSaving(true);
    try {
      await api.post(`/chat/${chatId}/agreement`, {
        agreed_price_kobo: Math.round(parseFloat(agrPrice) * 100),
        job_scope: agrScope,
        timeline: agrTimeline,
      });
      toast("Agreement proposed!", "success");
      setShowAgreement(false);
      fetchChat();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed", "error");
    } finally {
      setAgrSaving(false);
    }
  }

  async function confirmAgreement() {
    try {
      await api.post(`/chat/${chatId}/agreement/confirm`, {});
      toast("Confirmed!", "success");
      fetchChat();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed", "error");
    }
  }

  async function createEscrow() {
    try {
      const res = await api.post<{ escrow_account: string; amount_naira: number }>(`/chat/${chatId}/escrow/create`, {});
      toast(`Escrow created! Transfer ₦${res.data.amount_naira} to ${res.data.escrow_account}`, "success");
      fetchEscrow(); fetchChat();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed", "error");
    }
  }

  async function releasePayment() {
    try {
      await api.post(`/chat/${chatId}/escrow/release`, {});
      toast("Payment released!", "success");
      fetchEscrow(); fetchChat();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed", "error");
    }
  }

  async function markComplete() {
    try {
      await api.post(`/chat/${chatId}/complete`, {});
      toast("Job marked complete!", "success");
      fetchChat();
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed", "error");
    }
  }

  if (loading) return (
    <div className="flex min-h-dvh items-center justify-center bg-background">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>
  );

  if (!chat) return null;

  const isEmployer = chat.role === "employer";
  const agreement = chat.agreement;
  const myConfirmed = isEmployer ? agreement?.confirmed_by_employer : agreement?.confirmed_by_worker;

  return (
    <div className="flex flex-col h-dvh bg-background">
      {/* Header */}
      <div className="bg-hero-pattern px-4 pt-12 pb-4 flex items-center gap-3 flex-shrink-0">
        <button onClick={() => router.back()} className="text-white/70 hover:text-white">
          <ChevronLeft className="h-6 w-6" />
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-white truncate">{chat.job_description.slice(0, 50)}</p>
          <p className="text-xs text-white/50">
            {isEmployer ? "You're the employer" : "You're the worker"} · {chat.job_status.replace(/_/g, " ")}
          </p>
        </div>
      </div>

      {/* Agreement / Escrow banner */}
      {agreement && (
        <div className={cn(
          "mx-3 mt-2 rounded-2xl p-3 flex-shrink-0",
          agreement.locked
            ? "bg-gold-light border border-gold/30"
            : "bg-warning-light border border-warning/30"
        )}>
          {agreement.locked ? (
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <Lock className="h-4 w-4 text-gold-dark" />
                <p className="text-xs font-bold text-gold-foreground">Agreement Locked</p>
              </div>
              <p className="text-xs text-gold-foreground/70">
                {formatNaira(agreement.agreed_price_kobo!)} · {agreement.job_scope?.slice(0, 60)}
              </p>
              {isEmployer && !escrow && (
                <Button size="sm" className="mt-2.5 w-full bg-gold text-gold-foreground hover:bg-gold/90" onClick={createEscrow}>
                  <Wallet className="h-4 w-4" /> Create Escrow & Fund Job
                </Button>
              )}
              {isEmployer && escrow && escrow.status === "pending" && (
                <div className="mt-2 rounded-xl bg-white p-3">
                  <p className="text-xs font-bold text-foreground">Transfer {formatNaira(escrow.amount_kobo)} to:</p>
                  <p className="font-mono text-lg font-extrabold text-primary">{escrow.account_number}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Fund this account to activate the job</p>
                </div>
              )}
              {isEmployer && escrow?.status === "funded" && chat.job_status === "completed" && (
                <Button size="sm" className="mt-2.5 w-full" onClick={releasePayment}>
                  <CheckCircle className="h-4 w-4" /> Release Payment to Worker
                </Button>
              )}
              {!isEmployer && escrow?.status === "funded" && chat.job_status !== "completed" && (
                <Button size="sm" className="mt-2.5 w-full" onClick={markComplete}>
                  ✓ Mark Job Complete
                </Button>
              )}
            </div>
          ) : (
            <div>
              <p className="text-xs font-bold text-warning mb-1">Agreement Proposed</p>
              <p className="text-xs text-warning/80">
                {formatNaira(agreement.agreed_price_kobo!)} · {agreement.job_scope?.slice(0, 40)}
              </p>
              <div className="flex items-center gap-2 mt-2">
                <span className={cn("text-[10px] px-2 py-0.5 rounded-full font-semibold",
                  agreement.confirmed_by_employer ? "bg-success-light text-success" : "bg-muted text-muted-foreground"
                )}>
                  Employer {agreement.confirmed_by_employer ? "✓" : "…"}
                </span>
                <span className={cn("text-[10px] px-2 py-0.5 rounded-full font-semibold",
                  agreement.confirmed_by_worker ? "bg-success-light text-success" : "bg-muted text-muted-foreground"
                )}>
                  Worker {agreement.confirmed_by_worker ? "✓" : "…"}
                </span>
              </div>
              {!myConfirmed && (
                <Button size="sm" className="mt-2.5 w-full" onClick={confirmAgreement}>
                  Confirm Agreement
                </Button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2 min-h-0">
        {chat.messages.map((msg) => (
          <MessageBubble key={msg.message_id} msg={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      {agreement?.locked && chat.job_status === "completed" ? (
        <div className="px-4 py-3 bg-white border-t border-border/60 text-center flex-shrink-0">
          <p className="text-xs text-muted-foreground">Job completed. Chat locked.</p>
        </div>
      ) : (
        <div className="bg-white border-t border-border/60 px-4 py-3 flex-shrink-0">
          {!agreement?.locked && (
            <button
              onClick={() => setShowAgreement(!showAgreement)}
              className="mb-2 text-xs font-bold text-primary hover:underline"
            >
              {showAgreement ? "Cancel" : "+ Propose / Edit Agreement"}
            </button>
          )}

          {showAgreement && (
            <div className="mb-3 space-y-2 rounded-2xl bg-accent/40 border border-accent p-3">
              <Input label="Price (₦)" type="number" placeholder="e.g. 15000" value={agrPrice}
                onChange={(e) => setAgrPrice(e.target.value)} />
              <Input label="Job scope" placeholder="What exactly will be done?" value={agrScope}
                onChange={(e) => setAgrScope(e.target.value)} />
              <Input label="Timeline" placeholder="e.g. 2 days starting tomorrow" value={agrTimeline}
                onChange={(e) => setAgrTimeline(e.target.value)} />
              <Button size="sm" className="w-full" loading={agrSaving}
                disabled={!agrPrice || !agrScope || !agrTimeline} onClick={proposeAgreement}>
                Propose Agreement
              </Button>
            </div>
          )}

          <form onSubmit={sendMessage} className="flex gap-2">
            <input
              className="flex-1 rounded-2xl border-2 border-border bg-background px-4 py-2.5 text-sm focus:border-primary focus:outline-none text-foreground placeholder:text-muted-foreground/60"
              placeholder="Type a message…"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <button
              type="submit"
              disabled={!text.trim() || sending}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white disabled:opacity-40 hover:bg-primary/90 transition-colors"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

function MessageBubble({ msg }: { msg: Message }) {
  if (msg.message_type === "system") {
    return (
      <div className="flex justify-center">
        <span className="rounded-full bg-muted px-3 py-1 text-[10px] text-muted-foreground font-medium">
          {msg.content}
        </span>
      </div>
    );
  }

  return (
    <div className={cn("flex", msg.is_mine ? "justify-end" : "justify-start")}>
      <div className={cn(
        "max-w-[75%] rounded-2xl px-4 py-2.5 shadow-card",
        msg.is_mine
          ? "bg-primary text-white rounded-br-sm"
          : "bg-white text-foreground rounded-bl-sm border border-border/40"
      )}>
        <p className="text-sm">{msg.content}</p>
        <p className={cn("text-[10px] mt-0.5", msg.is_mine ? "text-white/50" : "text-muted-foreground")}>
          {new Date(msg.timestamp).toLocaleTimeString("en-NG", { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
    </div>
  );
}
