"use client";
import { useEffect, useRef, useState } from "react";
import { WS_BASE } from "./api";

export type LiveHit = {
  mint: string;
  symbol?: string | null;
  name?: string | null;
  dex: string;
  liquidity_usd: number;
  price_usd: number | null;
  launched_at: string | null;
};

export function useLiveHits() {
  const [hits, setHits] = useState<LiveHit[]>([]);
  const ref = useRef<WebSocket | null>(null);

  useEffect(() => {
    let retry: number | null = null;
    const connect = () => {
      const ws = new WebSocket(`${WS_BASE}/ws/live`);
      ref.current = ws;
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data) as LiveHit;
          setHits((prev) => [msg, ...prev].slice(0, 50));
        } catch {}
      };
      ws.onclose = () => {
        retry = window.setTimeout(connect, 2000);
      };
    };
    connect();
    return () => {
      if (retry) window.clearTimeout(retry);
      ref.current?.close();
    };
  }, []);

  return hits;
}
