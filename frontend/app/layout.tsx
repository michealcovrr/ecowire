import type { Metadata, Viewport } from "next";
import Script from "next/script";
import "./globals.css";
import { ToastProvider } from "@/components/ui/toast";

export const metadata: Metadata = {
  title: "EcoNet",
  description: "Your community financial identity",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "EcoNet",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#0F3D2E",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/* CSS variable bridge — fonts load async so UI renders immediately with system-font fallback */}
        <style dangerouslySetInnerHTML={{ __html: `
          :root {
            --font-jakarta: "Plus Jakarta Sans";
            --font-inter: "Inter";
          }
        `}} />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
      </head>
      <body>
        <ToastProvider>{children}</ToastProvider>
        <Script
          id="gfonts"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `(function(){var l=document.createElement('link');l.rel='stylesheet';l.href='https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap';document.head.appendChild(l);})();`,
          }}
        />
      </body>
    </html>
  );
}
