"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { MessageSquare, ChevronRight } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

interface Chat {
  chat_id: string;
  job_description: string;
  job_status: string;
  role: "employer" | "worker";
  other_user_name: string;
  last_message: string | null;
  last_message_at: string;
}

const JOB_STATUS_BADGE: Record<string, "default" | "success" | "accent" | "gold" | "destructive" | "warning" | "secondary"> = {
  open: "secondary",
  matched: "accent",
  agreement_locked: "gold",
  funded: "warning",
  active: "success",
  completed: "secondary",
  disputed: "destructive",
};

export default function ChatListPage() {
  const router = useRouter();
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<{ chats: Chat[] }>("/chat/my")
      .then((r) => setChats(r.data.chats ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col min-h-dvh pb-6">
      <div className="bg-hero-pattern px-5 pt-12 pb-5">
        <h1 className="text-xl font-extrabold text-white">Job Chats</h1>
        <p className="text-sm text-white/60 mt-0.5">Negotiations and agreements</p>
      </div>

      <div className="px-4 pt-4 space-y-2">
        {loading ? (
          [1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)
        ) : chats.length === 0 ? (
          <div className="rounded-2xl bg-white border border-border/40 shadow-card p-8 text-center mt-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted mx-auto mb-3">
              <MessageSquare className="h-7 w-7 text-muted-foreground" />
            </div>
            <p className="text-sm font-bold text-foreground">No chats yet</p>
            <p className="text-xs text-muted-foreground mt-1">Accept a worker on a job to start chatting.</p>
          </div>
        ) : (
          chats.map((chat) => (
            <button
              key={chat.chat_id}
              onClick={() => router.push(`/chat/${chat.chat_id}`)}
              className="w-full flex items-center gap-3 rounded-2xl bg-white border border-border/40 shadow-card p-4 text-left hover:shadow-card-md transition-shadow"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 flex-shrink-0">
                <MessageSquare className="h-6 w-6 text-primary" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-bold text-foreground truncate">{chat.other_user_name}</p>
                  <span className="text-[10px] text-muted-foreground flex-shrink-0">
                    {new Date(chat.last_message_at).toLocaleDateString("en-NG", { day: "numeric", month: "short" })}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground truncate mt-0.5">{chat.job_description}</p>
                {chat.last_message && (
                  <p className="text-xs text-muted-foreground/70 truncate mt-0.5">{chat.last_message}</p>
                )}
              </div>
              <div className="flex flex-col items-end gap-2 flex-shrink-0">
                <Badge variant={JOB_STATUS_BADGE[chat.job_status] ?? "secondary"}>
                  {chat.job_status.replace(/_/g, " ")}
                </Badge>
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
