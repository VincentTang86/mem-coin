import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SOL Meme Monitor",
  description: "Monitor newly launched Solana meme coins",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="max-w-7xl mx-auto p-6">{children}</div>
      </body>
    </html>
  );
}
