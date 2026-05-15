"use client";

import { useAuthStore } from "@/store/auth";
import { useRouter } from "next/navigation";
import { LogOut, ShieldCheck, HelpCircle, Users, ChevronRight, Bell } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";

const MORE_ITEMS = [
  {
    icon: ShieldCheck,
    label: "KYC & Verification",
    description: "Upgrade your identity tier",
    href: "/profile/kyc-upgrade",
    iconBg: "bg-accent",
    iconColor: "text-primary",
  },
  {
    icon: Users,
    label: "Community Circles",
    description: "Your local trusted network",
    href: "/community",
    iconBg: "bg-accent",
    iconColor: "text-primary",
  },
  {
    icon: Bell,
    label: "Notifications",
    description: "Activity and alerts",
    href: "/notifications",
    iconBg: "bg-amber-50",
    iconColor: "text-amber-600",
  },
  {
    icon: HelpCircle,
    label: "Help & Support",
    description: "FAQs and contact",
    href: "/help",
    iconBg: "bg-violet-50",
    iconColor: "text-violet-600",
  },
];

export default function MorePage() {
  const { logout, user } = useAuthStore();
  const router = useRouter();

  const initials = user?.full_name?.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase() ?? "?";
  const kycTier = user?.kyc_tier ?? 1;
  const kycLabel = ["", "Tier 1 — Basic", "Tier 2 — Verified", "Tier 3 — Full"][kycTier];

  function handleLogout() {
    logout();
    router.replace("/auth/phone");
  }

  return (
    <div className="flex flex-col pb-6">
      {/* Profile header */}
      <div className="bg-hero-pattern px-5 pt-12 pb-8">
        <div className="flex items-center gap-4">
          <Avatar size="lg">
            <AvatarFallback className="text-white bg-white/20 border border-white/30 text-lg">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="text-lg font-bold text-white">{user?.full_name ?? "User"}</p>
            <p className="text-xs text-white/50 font-mono">{user?.user_id}</p>
            <Badge variant="secondary" className="mt-1.5 text-[10px]">{kycLabel}</Badge>
          </div>
        </div>
      </div>

      <div className="px-4 mt-5 space-y-2">
        {MORE_ITEMS.map(({ icon: Icon, label, description, href, iconBg, iconColor }) => (
          <button
            key={href}
            onClick={() => router.push(href)}
            className="flex w-full items-center gap-4 rounded-2xl bg-white border border-border/40 shadow-card p-4 text-left hover:shadow-card-md transition-shadow"
          >
            <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${iconBg} flex-shrink-0`}>
              <Icon className={`h-5 w-5 ${iconColor}`} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-foreground">{label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
            </div>
            <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          </button>
        ))}

        <div className="pt-2">
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-4 rounded-2xl bg-white border border-destructive/20 shadow-card p-4 text-left hover:shadow-card-md transition-shadow"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-destructive-light flex-shrink-0">
              <LogOut className="h-5 w-5 text-destructive" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-bold text-destructive">Log Out</p>
            </div>
          </button>
        </div>
      </div>

      <p className="mt-8 text-center text-xs text-muted-foreground">
        alwi v0.1 · GTCO Squad Hackathon 3.0
      </p>
    </div>
  );
}
