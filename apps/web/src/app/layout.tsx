import type { Metadata, Viewport } from "next";
import { Inter, Noto_Sans_Bengali } from "next/font/google";
import { AppShell } from "@/components/AppShell";
import "./globals.css";

const latin = Inter({ variable: "--font-latin", subsets: ["latin"] });
const bangla = Noto_Sans_Bengali({ variable: "--font-bangla", subsets: ["bengali"], weight: ["400", "500", "600", "700"] });

export const metadata: Metadata = {
  title: "AirWindow BD",
  description: "Plan outdoor time around measured air quality and short-term PM2.5/PM10 forecasts in Bangladesh.",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f4f4f6" },
    { media: "(prefers-color-scheme: dark)", color: "#000000" },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${latin.variable} ${bangla.variable} font-sans antialiased`}>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
