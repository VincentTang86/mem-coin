export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
export const WS_BASE = process.env.NEXT_PUBLIC_WS_BASE || "ws://localhost:8000";

export type TokenOut = {
  mint: string;
  symbol: string | null;
  name: string | null;
  source: string;
  launched_at: string | null;
  metadata_uri: string | null;
  best_pool_address: string | null;
  best_dex: string | null;
  liquidity_usd: number | null;
  price_usd: number | null;
  age_hours: number | null;
};

export type TokenListResponse = {
  items: TokenOut[];
  total: number;
  page: number;
  page_size: number;
};

export async function fetchJson<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}
