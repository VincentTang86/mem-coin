"use client";
import Link from "next/link";
import type { TokenOut } from "@/lib/api";

const fmtUsd = (v: number | null | undefined) =>
  v == null ? "—" : `$${v >= 1000 ? v.toLocaleString(undefined, { maximumFractionDigits: 0 }) : v.toFixed(6)}`;

const fmtAge = (h: number | null | undefined) => {
  if (h == null) return "—";
  if (h < 1) return `${Math.round(h * 60)}m`;
  if (h < 24) return `${h.toFixed(1)}h`;
  return `${(h / 24).toFixed(1)}d`;
};

export default function TokenTable({ items, highlight }: { items: TokenOut[]; highlight: Set<string> }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-800">
      <table className="w-full text-sm">
        <thead className="bg-zinc-900 text-zinc-400">
          <tr>
            <th className="text-left px-3 py-2">Token</th>
            <th className="text-left px-3 py-2">DEX</th>
            <th className="text-right px-3 py-2">Liquidity</th>
            <th className="text-right px-3 py-2">Price</th>
            <th className="text-right px-3 py-2">Age</th>
            <th className="text-left px-3 py-2">Mint</th>
          </tr>
        </thead>
        <tbody>
          {items.map((t) => (
            <tr
              key={t.mint}
              className={
                "border-t border-zinc-900 hover:bg-zinc-900/60 " +
                (highlight.has(t.mint) ? "bg-indigo-950/40" : "")
              }
            >
              <td className="px-3 py-2">
                <Link href={`/tokens/${t.mint}`} className="hover:text-indigo-400">
                  <span className="font-medium">{t.symbol || "?"}</span>{" "}
                  <span className="text-zinc-500">{t.name}</span>
                </Link>
              </td>
              <td className="px-3 py-2 text-zinc-400">{t.best_dex}</td>
              <td className="px-3 py-2 text-right">{fmtUsd(t.liquidity_usd)}</td>
              <td className="px-3 py-2 text-right">{fmtUsd(t.price_usd)}</td>
              <td className="px-3 py-2 text-right">{fmtAge(t.age_hours)}</td>
              <td className="px-3 py-2 font-mono text-xs text-zinc-500">
                {t.mint.slice(0, 6)}…{t.mint.slice(-4)}
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={6} className="px-3 py-12 text-center text-zinc-500">
                暂无命中
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
