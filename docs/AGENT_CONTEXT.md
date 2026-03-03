# ArbitrageVault BookFinder — Agent Context

**Version**: 1.0 — March 2026
**Purpose**: Context file for AI agents (OpenClaw, N8N, etc.) consuming this API.
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
| `bsr` | int | Best Sellers Rank at scan time |
| `category` | string | Keepa category (e.g. "Medical Books") |
| `estimated_buy_price` | float | current_price × 0.50 (sourcing estimate) |

### condition_signal rules (Phase C, shipped March 2026)
- **STRONG**: used ROI >= 25% AND <= 10 competing used sellers
- **MODERATE**: used ROI >= 10% AND <= 25 competing used sellers
- **WEAK**: low used ROI or too much competition
- **UNKNOWN**: no used price data available

Confidence score is boosted +10 (STRONG) or +5 (MODERATE).

---

## Classification System

Picks are classified into 5 categories. Priority order: first match wins.

| Category | Criteria | Action |
|----------|----------|--------|
| **REJECT** | Amazon on listing, OR ROI < 0, OR BSR <= 0, OR WEAK condition + ROI < 5% | Do not buy |
| **FLUKE** | No history (first time seen) | Ignore — not enough data |
| **JACKPOT** | ROI > 80% with history | Manual verification required — check for data errors |
| **REVENANT** | Last seen 24h+ ago, reappears today | Monitor — recurring pattern |
| **STABLE** | 2+ sightings, ROI 15-80%, BSR > 0, no Amazon | Recommended buy — human reviews |

**Critical**: JACKPOT is never auto-acted on. High ROI + history sounds great but
often signals a data anomaly, a price spike, or a condition error. Human eyes required.

---

## API Endpoints for Agents

### Authentication
- Human users: Firebase Bearer token (`Authorization: Bearer <token>`)
- Agents/N8N: API Key header (`X-API-Key: avk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)

API keys are scoped. Request only the scopes you need.

### Key Endpoints

| Endpoint | Method | Scope | Description |
|----------|--------|-------|-------------|
| `/api/v1/daily-review/actionable` | GET | `daily_review:read` | STABLE-only pre-filtered buy list, sorted by stability then ROI |
| `/api/v1/daily-review/today` | GET | `daily_review:read` | Full classified review with all 5 categories and counts |
| `/api/v1/autosourcing/run-custom` | POST | `autosourcing:write` | Trigger a new sourcing scan |
| `/api/v1/autosourcing/jobs/{id}` | GET | `autosourcing:read` | Poll job status and results |

### Actionable Buy List — Example Response

```json
{
  "items": [
    {
      "asin": "0134685997",
      "title": "The Pragmatic Programmer",
      "category": "Computers & Technology",
      "current_price": 45.00,
      "estimated_buy_price": 22.50,
      "roi_percentage": 28.5,
      "stability_score": 74,
      "confidence_score": 81,
      "velocity_score": 62,
      "bsr": 12450,
      "overall_rating": "GOOD",
      "classification": "STABLE",
      "action_recommendation": "BUY"
    }
  ],
  "total_found": 3,
  "filters_applied": {"min_roi": 15.0, "max_results": 10, "classification": "STABLE"},
  "generated_at": "2026-03-03T07:00:00+00:00"
}
```

### Webhook — Job Completion Notification

When a scan completes, the backend POSTs to configured webhook URLs:

```json
{
  "event": "autosourcing.job.completed",
  "timestamp": "2026-03-03T07:04:32+00:00",
  "data": {
    "job_id": "uuid",
    "user_id": "uuid",
    "picks_count": 18,
    "stable_count": 4,
    "duration_seconds": 47.2
  }
}
```

Header `X-Webhook-Signature: sha256=<hmac>` for payload verification.

---

## What Agents Can and Cannot Do

### Can do
- Read the daily actionable buy list and summarize it
- Explain why a pick is STABLE (interpret the scores)
- Compare two picks and recommend which to examine first
- Alert the human if a JACKPOT appears and explain why manual verification is needed
- Trigger a sourcing scan and poll for results
- Receive webhook notifications when scans complete

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
    → POST /autosourcing/run-custom  (trigger scan)
    → Wait for webhook: autosourcing.job.completed
    → GET /daily-review/actionable   (fetch STABLE picks)
    → Send Telegram/Slack with top 5
```

Failure modes to handle:
- Scan timeout: configure N8N timeout to 20 min
- API down: retry policy 3 attempts with backoff
- Empty list: send "No STABLE picks this morning" message rather than silence

---

## Production URLs

| Service | URL |
|---------|-----|
| Backend API | https://arbitragevault-backend-v2.onrender.com |
| Frontend | https://arbitragevault.netlify.app |
| API Docs | https://arbitragevault-backend-v2.onrender.com/docs |

---

## Multi-Niche Strategy (March 2026)

The system is not textbook-only. The AutoSourcing engine supports any Keepa category.
Current validated categories: Books, Programming, Computer Science, Medical, Engineering,
Business, Accounting, Education, Science.

The scoring logic (velocity, stability, condition) is category-agnostic.
Target profile: ROI >= 20%, rotation <= 30 days, <= 8 FBA competitors, Amazon not on listing.
