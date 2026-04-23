"use client";
import { useEffect, useState } from "react";

export type FilterState = {
  max_age_hours: number;
  min_liquidity_usd: number;
  dex: string;
  sort: "liquidity_usd" | "launched_at" | "price_usd";
  order: "asc" | "desc";
};

const DEFAULTS: FilterState = {
  max_age_hours: 72,
  min_liquidity_usd: 10000,
  dex: "",
  sort: "liquidity_usd",
  order: "desc",
};

const LS_KEY = "memcoin:saved_filters";

type Saved = { name: string; payload: FilterState };

export default function FilterPanel({
  value,
  onChange,
}: {
  value: FilterState;
  onChange: (f: FilterState) => void;
}) {
  const [saved, setSaved] = useState<Saved[]>([]);
  const [name, setName] = useState("");

  useEffect(() => {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (raw) setSaved(JSON.parse(raw));
    } catch {}
  }, []);

  const persist = (next: Saved[]) => {
    setSaved(next);
    localStorage.setItem(LS_KEY, JSON.stringify(next));
  };

  return (
    <div className="bg-zinc-900 rounded-lg p-4 grid grid-cols-2 md:grid-cols-6 gap-3 text-sm">
      <label className="flex flex-col">
        <span className="text-zinc-400">最大发行 (小时)</span>
        <input
          type="number"
          className="bg-zinc-800 rounded px-2 py-1"
          value={value.max_age_hours}
          onChange={(e) => onChange({ ...value, max_age_hours: +e.target.value })}
        />
      </label>
      <label className="flex flex-col">
        <span className="text-zinc-400">最小 Liquidity (USD)</span>
        <input
          type="number"
          className="bg-zinc-800 rounded px-2 py-1"
          value={value.min_liquidity_usd}
          onChange={(e) => onChange({ ...value, min_liquidity_usd: +e.target.value })}
        />
      </label>
      <label className="flex flex-col">
        <span className="text-zinc-400">DEX</span>
        <select
          className="bg-zinc-800 rounded px-2 py-1"
          value={value.dex}
          onChange={(e) => onChange({ ...value, dex: e.target.value })}
        >
          <option value="">全部</option>
          <option value="pumpfun_bonding">Pump.fun</option>
          <option value="raydium_amm">Raydium AMM</option>
          <option value="raydium_clmm">Raydium CLMM</option>
        </select>
      </label>
      <label className="flex flex-col">
        <span className="text-zinc-400">排序</span>
        <select
          className="bg-zinc-800 rounded px-2 py-1"
          value={value.sort}
          onChange={(e) => onChange({ ...value, sort: e.target.value as FilterState["sort"] })}
        >
          <option value="liquidity_usd">Liquidity</option>
          <option value="launched_at">发行时间</option>
          <option value="price_usd">价格</option>
        </select>
      </label>
      <label className="flex flex-col">
        <span className="text-zinc-400">方向</span>
        <select
          className="bg-zinc-800 rounded px-2 py-1"
          value={value.order}
          onChange={(e) => onChange({ ...value, order: e.target.value as "asc" | "desc" })}
        >
          <option value="desc">降序</option>
          <option value="asc">升序</option>
        </select>
      </label>
      <div className="flex items-end gap-1">
        <input
          placeholder="预设名"
          className="bg-zinc-800 rounded px-2 py-1 flex-1 min-w-0"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          className="bg-indigo-600 hover:bg-indigo-500 rounded px-2 py-1"
          onClick={() => {
            if (!name) return;
            persist([...saved.filter((s) => s.name !== name), { name, payload: value }]);
            setName("");
          }}
        >
          保存
        </button>
      </div>
      {saved.length > 0 && (
        <div className="col-span-full flex flex-wrap gap-2 pt-2 border-t border-zinc-800">
          <span className="text-zinc-400">预设:</span>
          {saved.map((s) => (
            <span key={s.name} className="inline-flex items-center gap-1 bg-zinc-800 rounded px-2 py-0.5">
              <button className="hover:text-indigo-400" onClick={() => onChange(s.payload)}>
                {s.name}
              </button>
              <button
                className="text-zinc-500 hover:text-red-400 text-xs"
                onClick={() => persist(saved.filter((x) => x.name !== s.name))}
              >
                ×
              </button>
            </span>
          ))}
          <button className="text-zinc-400 hover:text-zinc-200 ml-auto" onClick={() => onChange(DEFAULTS)}>
            重置
          </button>
        </div>
      )}
    </div>
  );
}

export { DEFAULTS };
