"use client";

import * as React from "react";
import { Drawer as VaulDrawer } from "vaul";
import { cn } from "@/lib/utils";

interface DrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
  title?: string;
  snapPoints?: (string | number)[];
}

export function Drawer({ open, onOpenChange, children, title, snapPoints }: DrawerProps) {
  return (
    <VaulDrawer.Root
      open={open}
      onOpenChange={onOpenChange}
      snapPoints={snapPoints}
    >
      <VaulDrawer.Portal>
        <VaulDrawer.Overlay className="fixed inset-y-0 left-1/2 z-40 w-full max-w-[480px] -translate-x-1/2 bg-black/50" />
        <VaulDrawer.Content
          className={cn(
            "fixed bottom-0 left-1/2 z-50 w-full max-w-[480px] -translate-x-1/2",
            "flex flex-col rounded-t-3xl bg-white shadow-float outline-none",
            "max-h-[92dvh]"
          )}
        >
          {/* Drag handle */}
          <div className="flex justify-center pt-3 pb-1 flex-shrink-0">
            <div className="h-1 w-10 rounded-full bg-border" />
          </div>

          {title && (
            <div className="px-5 pb-3 flex-shrink-0">
              <h3 className="text-lg font-bold text-foreground">{title}</h3>
            </div>
          )}

          <div className="overflow-y-auto px-5 pb-10 flex-1">
            {children}
          </div>
        </VaulDrawer.Content>
      </VaulDrawer.Portal>
    </VaulDrawer.Root>
  );
}

export function DrawerTrigger({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <VaulDrawer.Trigger asChild>
      <div {...props}>{children}</div>
    </VaulDrawer.Trigger>
  );
}
