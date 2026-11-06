import type { Metadata } from "next";
import { Inter_Tight, JetBrains_Mono } from "next/font/google";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

const inter = Inter_Tight({ subsets: ["latin"], weight: ["300", "400", "500"], variable: "--font-inter-tight" });
const mono = JetBrains_Mono({ subsets: ["latin"], weight: ["400"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Undertow",
  description: "King tides soak Miami Beach roads from below. Undertow shows the hidden damage and the best repairs for a budget.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
