"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Briefcase, BarChart2, User, Wallet } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Home", icon: Home },
  { href: "/wallet", label: "Wallet", icon: Wallet },
  { href: "/jobs", label: "Jobs", icon: Briefcase },
  { href: "/finance", label: "Finance", icon: BarChart2 },
  { href: "/profile", label: "Profile", icon: User },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-1/2 z-40 w-full max-w-[480px] -translate-x-1/2 bg-white/95 backdrop-blur-sm border-t border-border/60 safe-bottom">
      <div className="flex items-stretch">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "relative flex flex-1 flex-col items-center justify-center gap-0.5 py-3 text-[10px] font-semibold transition-colors duration-200",
                active ? "text-primary" : "text-muted-foreground hover:text-foreground/70"
              )}
            >
              {active && (
                <motion.div
                  layoutId="nav-pill"
                  className="absolute inset-x-2 -top-px h-0.5 rounded-full bg-primary"
                  transition={{ type: "spring", stiffness: 500, damping: 40 }}
                />
              )}
              <motion.div
                animate={active ? { scale: 1.1 } : { scale: 1 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
              >
                <Icon
                  className="h-5 w-5"
                  strokeWidth={active ? 2.5 : 1.8}
                />
              </motion.div>
              <span>{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
