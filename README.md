# SOL Meme 币监控

实时监控 Solana 链上新发行的 meme 币，聚焦 Pump.fun / Raydium，筛选规则：
- 发行时间 ≤ 3 天 (72 小时)
- 链上流动池 Liquidity USD > $10,000

## 架构

- **后端**: FastAPI + Celery + Redis + SQLAlchemy 2.0 (async) + PostgreSQL
- **前端**: Next.js 14 (App Router) + TailwindCSS + SWR
- **数据源**: Pump.fun (`frontend-api.pump.fun`) · Raydium V3 (`api-v3.raydium.io`) · Solana RPC · Jupiter Price API
- **实时推送**: WebSocket (`/ws/live`) ←Redis Pub/Sub←Celery worker

## 快速开始

```bash
# 1. 启动依赖
docker compose up -d postgres redis

# 2. 初始化后端
cd backend
cp .env.example .env
pip install uv && uv pip install --system -e .[dev]
alembic upgrade head

# 3. 启动 API
uvicorn app.main:app --reload --port 8000

# 4. 启动 worker + beat（另开终端）
celery -A app.tasks.celery_app worker -B -l info

# 5. 启动前端（另开终端）
cd ../web
npm install
npm run dev
# → http://localhost:3000
```

或一键 docker-compose:

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

## 环境变量 (`backend/.env`)

见 `backend/.env.example`。Helius API key 可选（未设置则回落到公共 Solana RPC）。

## 核心接口

- `GET /api/tokens` — 支持 `max_age_hours` / `min_liquidity_usd` / `dex` / `sort` / `order` / `page` / `page_size`
- `GET /api/tokens/{mint}` — 单币详情 + 最近 200 条快照
- `GET/POST/DELETE /api/filters` — 自定义筛选器持久化
- `WS /ws/live` — 实时命中推送

## 调度

| 任务 | 频率 | 作用 |
|---|---|---|
| `discover_new` | 60s | 拉取 Pump.fun / Raydium 新币新池入库 |
| `refresh_pools` | 30s | 刷新 ≤3d 的 token 对应的池子流动性与价格，命中即推送 WS |

## 测试

```bash
cd backend && pytest
```

## 非目标（后续迭代）

用户系统 / 交易下单 / K 线图 / 告警 (TG/邮件) / 多链支持。
