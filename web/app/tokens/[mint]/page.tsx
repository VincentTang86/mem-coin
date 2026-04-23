"use client";
import Link from "next/link";
import useSWR from "swr";
import { fetchJson } from "@/lib/api";

type Detail = {
  token: { mint: string; symbol: string | null; name: string | null; source: string; launched_at: string | null; age_hours: number | null; metadata_uri: string | null };
  pools: { pool_address: string; dex: string; liquidity_usd: number | null; price_usd: number | null; updated_at: string }[];
  snapshots: { pool_address: string; ts: string; price_usd: number | null; liquidity_usd: number | null }[];
};

export default function TokenPage({ params }: { params: { mint: string } }) {
  const { data } = useSWR<Detail>(`/api/tokens/${params.mint}`, (k) => fetchJson(k), { refreshInterval: 10000 });

  if (!data) return <div className="text-zinc-500">加载中…</div>;
  const t = data.token;

  return (
    <main className="space-y-4">
      <Link href="/" className="text-sm text-zinc-400 hover:text-indigo-400">← 返回</Link>
      <header>
        <h1 className="text-2xl font-semibold">
          {t.symbol || "?"} <span className="text-zinc-500 text-base">{t.name}</span>
        </h1>
        <div className="text-xs font-mono text-zinc-500">{t.mint}</div>
      </header>

      <section className="grid grid-cols-3 gap-4 text-sm">
        <div className="bg-zinc-900 rounded p-3">
          <div className="text-zinc-400">来源</div>
          <div>{t.source}</div>
        </div>
        <div className="bg-zinc-900 rounded p-3">
          <div className="text-zinc-400">发行时间</div>
          <div>{t.launched_at ? new Date(t.launched_at).toLocaleString() : "—"}</div>
        </div>
        <div className="bg-zinc-900 rounded p-3">
          <div className="text-zinc-400">Age</div>
          <div>{t.age_hours?.toFixed(1)} h</div>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-medium mb-2">池子</h2>
        <table className="w-full text-sm border border-zinc-800 rounded">
          <thead className="bg-zinc-900 text-zinc-400">
            <tr><th className="text-left px-3 py-2">DEX</th><th className="text-left px-3 py-2">Pool</th><th className="text-right px-3 py-2">Liquidity</th><th className="text-right px-3 py-2">Price</th></tr>
          </thead>
          <tbody>
            {data.pools.map((p) => (
              <tr key={p.pool_address} className="border-t border-zinc-900">
                <td className="px-3 py-2">{p.dex}</td>
                <td className="px-3 py-2 font-mono text-xs text-zinc-500">{p.pool_address.slice(0, 8)}…</td>
                <td className="px-3 py-2 text-right">${p.liquidity_usd?.toLocaleString() ?? "—"}</td>
                <td className="px-3 py-2 text-right">${p.price_usd ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section>
        <h2 className="text-lg font-medium mb-2">近期快照 ({data.snapshots.length})</h2>
        <div className="text-xs text-zinc-500">可在后续迭代接入 K 线图。</div>
      </section>
    </main>
  );
}
