import type { Metadata } from "next";
import { Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  title: "Crebit AI Studio",
  description: "AI-powered creative studio for generative content",
  icons: {
    icon: "/favicon.png",
    apple: "/favicon.png",
  },
};

import { LanguageProvider } from "@/contexts/LanguageContext";
import { SessionProvider } from "@/contexts/SessionContext";
import { DimensionConfigProvider } from "@/contexts/DimensionConfigContext";
import { DimensionChainProvider } from "@/contexts/DimensionChainContext";
import { ToastProvider } from "@/components/Toast";
import { ThemeProvider } from "@/components/theme-provider";
import { DNACardSidePanelPortal } from "@/components/dna-card/DNACardSidePanel";
import { NetworkStatusBadge } from "@/components/ui/NetworkStatusBadge";
import { PostHogProvider } from "@/app/providers/PostHogProvider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* PWA Manifest */}
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#c7873a" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />

        {/* Material Icons for Stitch AI design */}
        <link
          href="https://fonts.googleapis.com/icon?family=Material+Icons+Round"
          rel="stylesheet"
        />
        {/* Material Symbols Outlined for Academy icons */}
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200"
          rel="stylesheet"
        />
        {/* Inter font for body text */}
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
        {/* Noto Sans KR for Korean text (V5/V6/V7 Design System) */}
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={`${spaceGrotesk.variable} ${jetbrainsMono.variable} font-sans antialiased`} suppressHydrationWarning>
        <PostHogProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="light"
            enableSystem
            disableTransitionOnChange
          >
            <SessionProvider>
              <LanguageProvider>
                <DimensionConfigProvider>
                  <DimensionChainProvider>
                    <ToastProvider>
                      {/* Offline status indicator */}
                      <NetworkStatusBadge />
                      {children}
                      <DNACardSidePanelPortal />
                    </ToastProvider>
                  </DimensionChainProvider>
                </DimensionConfigProvider>
              </LanguageProvider>
            </SessionProvider>
          </ThemeProvider>
        </PostHogProvider>
      </body>
    </html>
  );
}
