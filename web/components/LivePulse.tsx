"use client";
import type { LiveHit } from "@/lib/ws";

export default function LivePulse({ hits }: { hits: LiveHit[] }) {
  return (
    <div className="flex items-center gap-2 text-xs text-zinc-400">
      <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
      <span>实时 · 已接收 {hits.length} 次命中</span>
      {hits[0] && (
        <span className="text-zinc-300">
          最新: <span className="text-emerald-400">{hits[0].symbol || hits[0].mint.slice(0, 6)}</span>
        </span>
      )}
    </div>
  );
}
