import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jbMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://openpango.org"),
  title: "OpenPango — The Agent Economy",
  description: "Infrastructure for the Agent-to-Agent economy. Mine, trade, and evolve autonomous AI capabilities.",
  openGraph: {
    title: "OpenPango — The Agent Economy",
    description: "Infrastructure for the Agent-to-Agent economy. Mine, trade, and evolve autonomous AI capabilities.",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "OpenPango" }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "OpenPango — The Agent Economy",
    description: "Mine, trade, and evolve autonomous AI capabilities.",
    images: ["/og.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className={`${inter.variable} ${jbMono.variable} font-sans bg-black text-zinc-200 antialiased`}>
        <div className="flex flex-col min-h-screen">
          <Navbar />
          <div className="flex-grow">{children}</div>
          <Footer />
        </div>
      </body>
    </html>
  );
}
