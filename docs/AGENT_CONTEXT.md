# ArbitrageVault BookFinder — Agent Context

**Version**: 2.1 — March 2026
**Purpose**: Context file for AI agents (CoWork, N8N, OpenClaw, etc.) consuming this API.
Load this file at session start to understand the business logic before querying endpoints.

---

## The Human Role (Non-Negotiable)

The human (Aziz) makes every buying decision. Always.
No agent, no automation system, no workflow ever places an order or commits money.

Agents exist to: surface information, trigger scans, classify results, and present
a clear morning briefing. The human looks at the list and decides what to buy.

---

## What the Business Does

Amazon book arbitrage: buy used/new books at a low price from one source,
sell them on Amazon FBA at a higher price, profit from the spread.

### The Strategy Pivot (November 3, 2025)

Before Nov 3 2025, the dominant strategy was "Prime Bump" — FBA sellers won
the Amazon Buy Box over FBM sellers even at higher prices, because Prime shipping
was weighted heavily.

Amazon changed the Buy Box algorithm: **Condition > Price > Shipping**.
Prime no longer protects a higher-priced seller. The Prime Bump is dead.

**The only viable model now: Intrinsic Value.**

A book has intrinsic value if real demand exists for it, independent of seller
positioning. The question is no longer "can I win the Buy Box with Prime?"
but "is this book worth more than what I'm paying, in absolute terms, today?"

---

## The Five Keepa Signals That Matter

All sourcing decisions flow through exactly five data points from the Keepa API:

1. **Lowest Used Price** — Current floor for used copies. Establishes the cost
   basis for arbitrage. If the lowest used is $8 and sourcing cost is $4, there's
   potential spread. If the lowest used is $6, margin is tight.

2. **Sales Rank Drops** — How often does the BSR (Best Sellers Rank) drop sharply?
   Each drop = a sale. High drop frequency = high velocity = book moves fast.
   Slow movers tie up capital.

3. **Amazon Price** — When Amazon itself sells this book, it sets the price floor.
   A book where Amazon is on the listing at $12 means listing higher than ~$12 is
   not viable. A book where Amazon is NOT on the listing = open field for
   third-party sellers.

4. **Used Offer Count** — How many competing used sellers? Low count = scarcity
   premium, less price competition. High count = race to the bottom on price.

5. **Stock Quantity** — How much inventory do competing sellers have? Deep stock
   from one seller signals price anchor. Thin stock signals opportunity.

---

## Pick Scoring Fields

Every pick returned by the API has these fields:

| Field | Type | Meaning |
|-------|------|---------|
| `roi_percentage` | float | Estimated profit margin (%) |
| `velocity_score` | int 0-100 | How fast the book sells |
| `stability_score` | int 0-100 | Price/BSR consistency over time |
| `confidence_score` | int 0-100 | Data completeness/reliability |
| `condition_signal` | string | STRONG / MODERATE / WEAK / UNKNOWN |
| `fba_seller_count` | int | Competing FBA sellers |
| `amazon_on_listing` | bool | True = Amazon is a direct competitor |
| `bsr` | int | Best Sellers Rank at scan time (-1 = unknown) |
| `category` | string | Keepa category (e.g. "Medical Books") |
| `estimated_buy_price` | float | current_price x source_price_factor (default 0.40) |
| `data_quality` | string | full / degraded / unavailable |

### condition_signal rules (Phase C, March 2026)
- **STRONG**: used ROI >= 25% AND <= 10 competing used sellers → confidence +10
- **MODERATE**: used ROI >= 10% AND <= 25 competing used sellers → confidence +5
- **WEAK**: low used ROI or too much competition
- **UNKNOWN**: no used price data available

### data_quality flag (P2, March 2026)
- **full**: all data sources available, results reliable
- **degraded**: partial data (e.g. price history unavailable), results approximate
- **unavailable**: no data could be retrieved (DB error or empty scan)

---

## Classification System

Picks are classified into 5 categories. Priority order: first match wins.

| Category | Criteria | Action |
|----------|----------|--------|
| **REJECT** | Amazon on listing, OR ROI < 0, OR BSR <= 0, OR WEAK condition + ROI < 20% | Do not buy |
| **FLUKE** | No history (first time seen) | Ignore — not enough data |
| **JACKPOT** | ROI > 80% with history | Manual verification required — check for data errors |
| **REVENANT** | Last seen 24h+ ago, reappears today | Monitor — recurring pattern |
| **STABLE** | 2+ sightings, ROI 15-80%, BSR > 0, no Amazon | Recommended buy — human reviews |

**Critical**: JACKPOT is never auto-acted on. High ROI + history sounds great but
often signals a data anomaly, a price spike, or a condition error. Human eyes required.

---

## API Authentication

### CoWork Agent (you)
Use Bearer token authentication with `COWORK_API_TOKEN`:
```
Authorization: Bearer <COWORK_API_TOKEN>
```

### Other Agents / N8N
Use API Key header:
```
X-API-Key: avk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
Keys are scoped. Common scopes: `autosourcing:read`, `autosourcing:write`, `autosourcing:job_read`, `daily_review:read`.

---

## Rate Limiting (CoWork Endpoints)

- `GET /api/v1/cowork/*`: 30 requests/min per token
- `POST /api/v1/cowork/fetch-and-score`: 5 requests/min per token
- On limit: HTTP 429 + `Retry-After` header (seconds to wait)

---

## CoWork Agent Endpoints (6 total)

| Endpoint | Method | Rate Limit | Description |
|----------|--------|------------|-------------|
| `/api/v1/cowork/dashboard-summary` | GET | 30/min | System health + 24h stats + top picks + data_quality |
| `/api/v1/cowork/daily-buy-list` | GET | 30/min | STABLE picks filtered by confidence + data_quality |
| `/api/v1/cowork/fetch-and-score` | POST | 5/min | On-demand ASIN/ISBN scoring |
| `/api/v1/cowork/last-job-stats` | GET | 30/min | Stats from most recent AutoSourcing job |
| `/api/v1/cowork/keepa-balance` | GET | 30/min | Keepa token balance (cached 60s) |
| `/api/v1/cowork/jobs` | GET | 30/min | Paginated job list with status filter |

---

## Key Endpoints for N8N / Other Agents

| Endpoint | Method | Scope | Description |
|----------|--------|-------|-------------|
| `/api/v1/daily-review/actionable` | GET | `daily_review:read` | STABLE-only buy list, sorted by stability then ROI |
| `/api/v1/daily-review/today` | GET | `daily_review:read` | Full classified review with all 5 categories |
| `/api/v1/autosourcing/run-custom` | POST | `autosourcing:write` | Trigger a new sourcing scan |
| `/api/v1/autosourcing/jobs/{id}` | GET | `autosourcing:job_read` | Poll job status and results |

---

## Example Responses

### Daily Buy List
```json
{
  "items": [
    {
      "asin": "0134685997",
      "title": "The Pragmatic Programmer",
      "category": "Computers & Technology",
      "current_price": 45.00,
      "estimated_buy_price": 15.75,
      "roi_percentage": 28.5,
      "stability_score": 74,
      "confidence_score": 81,
      "velocity_score": 62,
      "condition_signal": "STRONG",
      "bsr": 12450,
      "classification": "STABLE",
      "action_recommendation": "BUY"
    }
  ],
  "total_found": 3,
  "data_quality": "full",
  "generated_at": "2026-03-26T07:00:00+00:00"
}
```

### Dashboard Summary
```json
{
  "system_health": "ok",
  "last_job": {
    "id": "uuid",
    "status": "success",
    "picks_count": 18,
    "stable_count": 4,
    "duration_seconds": 47.2
  },
  "stats_24h": {"total_jobs": 3, "total_picks": 52, "stable_picks": 11},
  "top_picks": [...],
  "data_quality": "full"
}
```

### Keepa Balance
```json
{"tokens_remaining": 1250, "cached": true, "cache_age_seconds": 23}
```

---

## Webhook — Job Completion Notification

When a scan completes, the backend POSTs to configured webhook URLs:

```json
{
  "event": "autosourcing.job.completed",
  "timestamp": "2026-03-26T07:04:32+00:00",
  "data": {
    "job_id": "uuid",
    "picks_count": 18,
    "stable_count": 4,
    "duration_seconds": 47.2
  }
}
```

Header `X-Webhook-Signature: sha256=<hmac>` for payload verification.

**Note**: If `stable_count > 0`, SMS (Textbelt) and email (Resend) notifications are also
sent automatically after webhook delivery. These are parallel channels, not webhook payloads.

---

## What Agents Can and Cannot Do

### Can do
- Read the daily actionable buy list and summarize it
- Explain why a pick is STABLE (interpret the scores)
- Compare two picks and recommend which to examine first
- Alert the human if a JACKPOT appears and explain why manual verification is needed
- Trigger a sourcing scan and poll for results
- Receive webhook notifications when scans complete
- Check Keepa token balance before triggering expensive scans
- Browse job history with status filters

### Cannot do
- Verify the physical condition of a book
- Confirm a sourcing price is available today (prices change hourly)
- Know if the human has the capital or storage space to buy
- Replace human judgment on a JACKPOT — that's why it's flagged for manual review
- Decide how much to buy or when to sell

---

## N8N Morning Flow (Reference Design)

```
[Schedule 7am]
    -> POST /autosourcing/run-custom         (trigger scan)
    -> Wait for webhook: autosourcing.job.completed
    -> GET /api/v1/cowork/daily-buy-list     (fetch STABLE picks)
    -> Send Telegram/Slack with top 5
```

Alternative (polling instead of webhook):
```
[Schedule 7am]
    -> POST /autosourcing/run-custom         (trigger scan, get job_id)
    -> Poll GET /autosourcing/jobs/{job_id}  (every 30s, max 20 min)
    -> When status=success: GET /daily-review/actionable
    -> Send morning briefing
```

Failure modes to handle:
- Scan timeout: configure N8N timeout to 20 min
- API down: retry policy 3 attempts with backoff
- Empty list: send "No STABLE picks this morning" message rather than silence
- Rate limit (429): respect `Retry-After` header before retry
- `data_quality: degraded`: mention in briefing that data may be incomplete

---

## Production URLs

| Service | URL |
|---------|-----|
| Backend API | https://arbitragevault-backend-v2.onrender.com |
| Frontend | https://arbitragevault.netlify.app |
| API Docs (Swagger) | https://arbitragevault-backend-v2.onrender.com/docs |

---

## Sourcing Strategies (Calibrated March 2026)

| Strategy | BSR max | ROI min | Profit min | Max FBA sellers |
|----------|---------|---------|------------|-----------------|
| textbook | 250,000 | 35% | $12 | 8 |
| velocity | 75,000 | 30% | $8 | 5 |
| balanced | 100,000 | 30% | $10 | 6 |

**Key parameters:**
- `source_price_factor = 0.40` (buy at 40% of sell price — online arbitrage model)
- `fba_fee_percentage = 0.22` (Amazon referral + closing + FBA fees for books)
- `reject_weak = true` with threshold 20% (WEAK condition + ROI < 20% = REJECT)

**Post-Prime-Bump 2026:** The FBA Prime advantage for Buy Box was eliminated Nov 2025.
Pricing is now based on intrinsic_median (Keepa historical median).
condition_signal STRONG = priority signal for Buy Box competitiveness.

## Multi-Niche Strategy (March 2026)

The system is not textbook-only. The AutoSourcing engine supports any Keepa category.
Current validated categories: Books, Programming, Computer Science, Medical, Engineering,
Business, Accounting, Education, Science.

The scoring logic (velocity, stability, condition) is category-agnostic.
Target profile: ROI >= 30%, min profit $8-12, rotation <= 30 days, <= 5-8 FBA competitors, Amazon not on listing.
