"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { ChevronLeft, Bell, Wallet, Briefcase, MessageSquare, AlertCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface Notification {
  id: string;
  type: "wallet" | "job" | "chat" | "system" | "kyc";
  title: string;
  body: string;
  read: boolean;
  created_at: string;
  action_url?: string;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  wallet: <Wallet className="h-5 w-5 text-primary" />,
  job: <Briefcase className="h-5 w-5 text-primary" />,
  chat: <MessageSquare className="h-5 w-5 text-violet-600" />,
  system: <Bell className="h-5 w-5 text-muted-foreground" />,
  kyc: <AlertCircle className="h-5 w-5 text-warning" />,
};

const TYPE_BG: Record<string, string> = {
  wallet: "bg-accent",
  job: "bg-accent",
  chat: "bg-violet-50",
  system: "bg-muted/50",
  kyc: "bg-warning-light",
};

export default function NotificationsPage() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<{ notifications: Notification[] }>("/notifications")
      .then((r) => setNotifications(r.data.notifications ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function markRead(id: string) {
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, read: true } : n));
    } catch {}
  }

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="flex flex-col pb-6">
      {/* Header */}
      <div className="bg-hero-pattern px-5 pt-12 pb-5">
        <button onClick={() => router.back()} className="flex items-center gap-1.5 text-sm text-white/70 hover:text-white mb-6">
          <ChevronLeft className="h-4 w-4" /> Back
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-extrabold text-white">Notifications</h1>
            {unreadCount > 0 && (
              <p className="text-sm text-white/60 mt-0.5">{unreadCount} unread</p>
            )}
          </div>
        </div>
      </div>

      <div className="px-4 mt-5 space-y-2">
        {loading ? (
          [1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-16" />)
        ) : notifications.length === 0 ? (
          <div className="rounded-2xl bg-white border border-border/40 shadow-card p-8 text-center mt-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted mx-auto mb-3">
              <Bell className="h-7 w-7 text-muted-foreground" />
            </div>
            <p className="text-sm font-bold text-foreground">All caught up!</p>
            <p className="text-xs text-muted-foreground mt-1">No notifications yet.</p>
          </div>
        ) : (
          notifications.map((notif) => (
            <button
              key={notif.id}
              onClick={() => {
                markRead(notif.id);
                if (notif.action_url) router.push(notif.action_url);
              }}
              className={cn(
                "w-full flex items-start gap-3 rounded-2xl border p-4 text-left transition-shadow",
                notif.read
                  ? "bg-white border-border/40 shadow-card"
                  : "bg-white border-primary/20 shadow-card-md"
              )}
            >
              <div className={cn("flex h-10 w-10 items-center justify-center rounded-xl flex-shrink-0", TYPE_BG[notif.type] ?? "bg-muted/50")}>
                {TYPE_ICONS[notif.type] ?? <Bell className="h-5 w-5 text-muted-foreground" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p className={cn("text-sm font-bold truncate", notif.read ? "text-foreground" : "text-foreground")}>
                    {notif.title}
                  </p>
                  {!notif.read && (
                    <div className="h-2 w-2 rounded-full bg-primary flex-shrink-0 mt-1.5" />
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">{notif.body}</p>
                <p className="text-[10px] text-muted-foreground mt-1">
                  {new Date(notif.created_at).toLocaleDateString("en-NG", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                </p>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
