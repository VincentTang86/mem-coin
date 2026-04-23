"use client";
import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";

import { fetchJson, type TokenListResponse } from "@/lib/api";
import { useLiveHits } from "@/lib/ws";
import FilterPanel, { DEFAULTS, type FilterState } from "@/components/FilterPanel";
import TokenTable from "@/components/TokenTable";
import LivePulse from "@/components/LivePulse";

export default function HomePage() {
  const [filter, setFilter] = useState<FilterState>(DEFAULTS);
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const qs = useMemo(() => {
    const p = new URLSearchParams({
      max_age_hours: String(filter.max_age_hours),
      min_liquidity_usd: String(filter.min_liquidity_usd),
      sort: filter.sort,
      order: filter.order,
      page: String(page),
      page_size: String(pageSize),
    });
    if (filter.dex) p.set("dex", filter.dex);
    return p.toString();
  }, [filter, page]);

  const { data, error, isLoading, mutate } = useSWR<TokenListResponse>(
    `/api/tokens?${qs}`,
    (k) => fetchJson<TokenListResponse>(k),
    { refreshInterval: 15000 }
  );

  const hits = useLiveHits();
  useEffect(() => {
    if (hits.length > 0) mutate();
  }, [hits.length, mutate]);

  const highlight = useMemo(() => new Set(hits.slice(0, 10).map((h) => h.mint)), [hits]);

  return (
    <main className="space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">SOL Meme 监控</h1>
        <LivePulse hits={hits} />
      </header>

      <FilterPanel value={filter} onChange={(f) => { setFilter(f); setPage(1); }} />

      {error && <div className="text-red-400 text-sm">加载失败: {String(error)}</div>}
      {isLoading && <div className="text-zinc-500 text-sm">加载中…</div>}

      <TokenTable items={data?.items || []} highlight={highlight} />

      <div className="flex items-center justify-between text-sm text-zinc-400">
        <span>总数: {data?.total ?? 0}</span>
        <div className="flex gap-2">
          <button
            className="px-3 py-1 rounded bg-zinc-800 disabled:opacity-40"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            上一页
          </button>
          <span>第 {page} 页</span>
          <button
            className="px-3 py-1 rounded bg-zinc-800 disabled:opacity-40"
            disabled={!data || page * pageSize >= data.total}
            onClick={() => setPage((p) => p + 1)}
          >
            下一页
          </button>
        </div>
      </div>
    </main>
  );
}
