# Phase 8.0: Advanced Analytics & Decision System

**Date creation:** 16 Novembre 2025
**Status:** Planification
**Timeline estime:** 3-4 semaines
**Prerequis:** Phase 7.0 Complete (AutoSourcing Safeguards)

---

## Vue d'Ensemble

### Objectif Principal
Transformer ArbitrageVault d'un outil de scoring basique en un systeme de decision intelligent base sur analytics avancees, modelisation risques, et historical data tracking.

### Principes Directeurs
1. **Data-driven decisions** - Toutes recommandations basees sur donnees reelles
2. **Risk-aware** - Identifier et quantifier risques business (dead inventory, storage costs)
3. **Long-term thinking** - Modele 45-60 jours avec storage fees
4. **Transparent scoring** - Expliquer chaque composante du score
5. **Historical learning** - Apprendre des runs precedents pour ameliorer predictions

---

## Phase 8.1: Advanced Analytics Engine

**Timeline:** 1 semaine (5-7 jours)
**Priority:** CRITICAL - Foundation pour tout le reste

### Objectifs
Enrichir le scoring actuel (ROI, velocity, stability) avec metriques avancees basees sur donnees Keepa historiques et analyse competitive.

### Features Detaillees

#### 1.1 Velocity Intelligence
**Objectif:** Predire vitesse vente basee sur trends BSR

**Metriques:**
```python
# BSR Trend Analysis
bsr_trend_7d = analyze_bsr_trend(asin, days=7)
bsr_trend_30d = analyze_bsr_trend(asin, days=30)
bsr_trend_90d = analyze_bsr_trend(asin, days=90)

# Seasonal Patterns
seasonal_factor = detect_seasonal_pattern(asin, category)

# Category Velocity Benchmarks
category_avg_bsr = get_category_benchmark(category, "avg_bsr")
velocity_percentile = calculate_percentile(current_bsr, category_avg_bsr)
```

**Scoring Algorithm:**
```python
def calculate_velocity_score_advanced(asin_data, category):
    base_velocity = current_velocity_score(asin_data.bsr)

    # Trend boost/penalty
    trend_modifier = 0
    if bsr_trend_7d < 0:  # BSR improving (lower = better)
        trend_modifier += 10
    elif bsr_trend_7d > 0:  # BSR worsening
        trend_modifier -= 10

    # Seasonal boost
    seasonal_modifier = seasonal_factor * 5

    # Category benchmark adjustment
    if velocity_percentile > 0.75:  # Top 25% in category
        trend_modifier += 15

    final_velocity = min(100, max(0, base_velocity + trend_modifier + seasonal_modifier))
    return final_velocity
```

**Deliverables:**
- [ ] `VelocityAnalyticsService` avec trend analysis
- [ ] Seasonal pattern detection (ML-based optional)
- [ ] Category benchmarks table (database)
- [ ] API endpoint `POST /api/v1/analytics/velocity`
- [ ] Unit tests (10+ scenarios)

---

#### 1.2 Price Stability Analysis
**Objectif:** Mesurer stabilite prix pour predire margins durables

**Metriques:**
```python
# Price Variance
price_history = get_keepa_price_history(asin, days=90)
price_variance = calculate_variance(price_history)
price_std_dev = calculate_std_dev(price_history)

# Coefficient of Variation
cv = price_std_dev / mean(price_history)
stability_score = 100 * (1 - min(1, cv))

# Competitive Pricing Index
competitor_prices = get_offers_prices(asin)
our_position = rank_price(target_price, competitor_prices)
```

**Scoring Algorithm:**
```python
def calculate_price_stability_score(asin_data):
    # Historical stability (60% weight)
    historical_stability = 100 * (1 - min(1, coefficient_of_variation))

    # Competitive position (30% weight)
    competitive_score = 0
    if our_position == 1:  # Cheapest
        competitive_score = 100
    elif our_position <= 3:  # Top 3
        competitive_score = 75
    else:
        competitive_score = max(0, 100 - (our_position * 10))

    # Trend stability (10% weight)
    trend_stability = 100 if abs(price_trend_30d) < 5 else 50

    final_score = (
        historical_stability * 0.6 +
        competitive_score * 0.3 +
        trend_stability * 0.1
    )
    return round(final_score, 2)
```

**Deliverables:**
- [ ] `PriceStabilityService` avec variance calculation
- [ ] Competitive pricing index
- [ ] API endpoint `POST /api/v1/analytics/price-stability`
- [ ] Integration tests avec real Keepa data

---

#### 1.3 ROI Net Calculation
**Objectif:** ROI reel apres TOUS les fees (pas juste referral + FBA)

**Fees Complets:**
```python
# Existing fees (Phase 7.0)
referral_fee = sale_price * 0.15
fba_fee = calculate_fba_fee(weight, dimensions)
prep_fee = 0.20
inbound_shipping = 0.40

# New fees (Phase 8.1)
return_rate = 0.05  # 5% return rate estimation
return_cost = (sale_price + fba_fee) * return_rate

damage_rate = 0.02  # 2% damage rate
damage_cost = buy_price * damage_rate

storage_fee_30d = calculate_storage_fee(dimensions, days=30)
storage_fee_60d = calculate_storage_fee(dimensions, days=60)

# Total costs
total_costs = (
    buy_price +
    referral_fee +
    fba_fee +
    prep_fee +
    inbound_shipping +
    return_cost +
    damage_cost +
    storage_fee_30d  # Default 30-day assumption
)

# Net profit
net_profit = sale_price - total_costs
roi_net = (net_profit / buy_price) * 100
```

**Deliverables:**
- [ ] `ROICalculatorService` avec fees complets
- [ ] Return/damage rate configuration (par categorie)
- [ ] Storage fee calculator (dimensions-based)
- [ ] API endpoint `POST /api/v1/analytics/roi-net`
- [ ] Comparison tool: ROI brut vs ROI net

---

#### 1.4 Competition Analysis
**Objectif:** Evaluer landscape competitive pour chaque ASIN

**Metriques:**
```python
# Seller Analysis
total_sellers = count_offers(asin)
fba_sellers = count_offers(asin, fulfillment="FBA")
fbm_sellers = count_offers(asin, fulfillment="FBM")
fba_ratio = fba_sellers / total_sellers if total_sellers > 0 else 0

# Amazon Presence
amazon_on_listing = check_amazon_presence(asin)
amazon_has_buybox = check_buybox_owner(asin) == "Amazon"

# Seller Evolution (trend)
seller_count_30d_ago = get_historical_seller_count(asin, days_ago=30)
seller_trend = total_sellers - seller_count_30d_ago

# Competition Score
competition_score = calculate_competition_score(
    total_sellers=total_sellers,
    fba_ratio=fba_ratio,
    amazon_present=amazon_on_listing,
    seller_trend=seller_trend
)
```

**Scoring Algorithm:**
```python
def calculate_competition_score(total_sellers, fba_ratio, amazon_present, seller_trend):
    # Base score (fewer sellers = higher score)
    if total_sellers == 0:
        base_score = 100
    elif total_sellers <= 3:
        base_score = 90
    elif total_sellers <= 5:
        base_score = 70
    elif total_sellers <= 10:
        base_score = 50
    else:
        base_score = max(0, 50 - (total_sellers - 10) * 5)

    # FBA ratio modifier
    fba_modifier = 0
    if fba_ratio > 0.7:  # High FBA competition
        fba_modifier = -10
    elif fba_ratio < 0.3:  # Low FBA competition
        fba_modifier = +10

    # Amazon presence penalty
    amazon_penalty = -30 if amazon_present else 0

    # Trend modifier
    trend_modifier = 0
    if seller_trend < 0:  # Sellers leaving
        trend_modifier = +10
    elif seller_trend > 2:  # Sellers joining fast
        trend_modifier = -10

    final_score = max(0, min(100, base_score + fba_modifier + amazon_penalty + trend_modifier))
    return final_score
```

**Deliverables:**
- [ ] `CompetitionAnalysisService`
- [ ] Amazon presence detection (Keepa API integration)
- [ ] Seller count historical tracking
- [ ] API endpoint `POST /api/v1/analytics/competition`
- [ ] E2E tests avec ASINs Amazon vs non-Amazon

---

### Acceptance Criteria Phase 8.1
- [ ] Velocity Intelligence: BSR trends (7/30/90 days) calculated
- [ ] Price Stability: Variance et competitive index working
- [ ] ROI Net: All fees included (returns, damages, storage)
- [ ] Competition Analysis: Seller count, Amazon presence, FBA ratio
- [ ] API endpoints: 4 nouveaux endpoints analytics
- [ ] Tests: 20+ unit tests, 5+ integration tests
- [ ] Documentation: API docs updated avec exemples

---

## Phase 8.2: Historical Data Layer

**Timeline:** 1 semaine (5-7 jours)
**Priority:** HIGH - Enable learning from past

### Objectifs
Sauvegarder tous les runs AutoSourcing, tracker ASINs dans le temps, et mesurer performance reelle vs predictions pour ameliorer algorithmes.

### Database Schema

```sql
-- ASIN Historical Tracking
CREATE TABLE asin_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asin VARCHAR(10) NOT NULL,
    tracked_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Pricing data
    price DECIMAL(10,2),
    lowest_fba_price DECIMAL(10,2),
    lowest_fbm_price DECIMAL(10,2),

    -- Sales rank
    bsr INTEGER,
    bsr_drops_30d INTEGER,
    bsr_drops_90d INTEGER,

    -- Competition
    seller_count INTEGER,
    fba_seller_count INTEGER,
    amazon_on_listing BOOLEAN,
    amazon_has_buybox BOOLEAN,

    -- Metadata
    category_id INTEGER,
    metadata JSONB,

    CONSTRAINT asin_history_unique UNIQUE (asin, tracked_at)
);

CREATE INDEX idx_asin_history_asin ON asin_history(asin);
CREATE INDEX idx_asin_history_tracked_at ON asin_history(tracked_at);

-- Run History
CREATE TABLE run_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES autosourcing_jobs(id),

    -- Configuration snapshot
    config_snapshot JSONB NOT NULL,

    -- Results summary
    total_products_discovered INTEGER NOT NULL,
    total_picks_selected INTEGER NOT NULL,
    avg_roi_predicted DECIMAL(5,2),
    avg_velocity_predicted DECIMAL(5,2),

    -- Performance metrics
    success_rate DECIMAL(5,2),
    avg_confidence_score DECIMAL(5,2),

    -- Execution metadata
    executed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    execution_time_seconds INTEGER,
    tokens_consumed INTEGER,

    CONSTRAINT run_history_job_unique UNIQUE (job_id)
);

CREATE INDEX idx_run_history_executed_at ON run_history(executed_at);

-- Decision Outcomes (Track what actually happened)
CREATE TABLE decision_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asin VARCHAR(10) NOT NULL,

    -- Initial decision
    decision VARCHAR(20) NOT NULL,  -- BUY, SKIP, WATCH
    decided_at TIMESTAMP NOT NULL DEFAULT NOW(),
    predicted_roi DECIMAL(5,2),
    predicted_velocity DECIMAL(5,2),
    buy_price DECIMAL(10,2),
    target_sell_price DECIMAL(10,2),

    -- Actual outcome (updated later)
    actual_outcome VARCHAR(20),  -- SOLD, UNSOLD, RETURNED, DEAD_INVENTORY
    actual_roi DECIMAL(5,2),
    actual_sell_price DECIMAL(10,2),
    time_to_sell_days INTEGER,
    outcome_updated_at TIMESTAMP,

    -- Metadata
    notes TEXT,
    metadata JSONB
);

CREATE INDEX idx_decision_outcomes_asin ON decision_outcomes(asin);
CREATE INDEX idx_decision_outcomes_decided_at ON decision_outcomes(decided_at);
CREATE INDEX idx_decision_outcomes_outcome ON decision_outcomes(actual_outcome);
```

### Services Implementation

#### 2.1 ASIN Tracking Service
```python
class ASINTrackingService:
    async def track_asin(self, asin: str, keepa_data: dict):
        """
        Save ASIN snapshot to history table
        """
        snapshot = ASINHistoryCreate(
            asin=asin,
            tracked_at=datetime.utcnow(),
            price=keepa_data.get('current_price'),
            lowest_fba_price=keepa_data.get('fba_price'),
            lowest_fbm_price=keepa_data.get('fbm_price'),
            bsr=keepa_data.get('sales_rank'),
            bsr_drops_30d=keepa_data.get('stats', {}).get('drops_30'),
            seller_count=keepa_data.get('offer_count'),
            amazon_on_listing=keepa_data.get('is_amazon'),
            category_id=keepa_data.get('category'),
            metadata=keepa_data
        )

        return await self.repository.create_asin_snapshot(snapshot)

    async def get_asin_trend(self, asin: str, days: int = 30):
        """
        Get historical trend for ASIN
        """
        history = await self.repository.get_asin_history(asin, days=days)

        return {
            "asin": asin,
            "price_trend": calculate_trend([h.price for h in history]),
            "bsr_trend": calculate_trend([h.bsr for h in history]),
            "seller_count_trend": calculate_trend([h.seller_count for h in history]),
            "datapoints": len(history)
        }
```

#### 2.2 Run History Service
```python
class RunHistoryService:
    async def save_run(self, job_id: str, config: dict, results: dict):
        """
        Save AutoSourcing run to history
        """
        run = RunHistoryCreate(
            job_id=job_id,
            config_snapshot=config,
            total_products_discovered=results['total_count'],
            total_picks_selected=len(results['picks']),
            avg_roi_predicted=calculate_avg([p.roi_percentage for p in results['picks']]),
            avg_velocity_predicted=calculate_avg([p.velocity_score for p in results['picks']]),
            execution_time_seconds=results['execution_time'],
            tokens_consumed=results['tokens_used']
        )

        return await self.repository.save_run_history(run)

    async def get_performance_metrics(self, days: int = 30):
        """
        Get aggregate performance metrics
        """
        runs = await self.repository.get_recent_runs(days=days)

        return {
            "total_runs": len(runs),
            "avg_products_per_run": calculate_avg([r.total_products_discovered for r in runs]),
            "avg_picks_per_run": calculate_avg([r.total_picks_selected for r in runs]),
            "avg_success_rate": calculate_avg([r.success_rate for r in runs]),
            "total_tokens_consumed": sum([r.tokens_consumed for r in runs])
        }
```

#### 2.3 Decision Outcome Tracking
```python
class DecisionOutcomeService:
    async def record_decision(self, pick: AutoSourcingPick, decision: str):
        """
        Record user decision on a pick
        """
        outcome = DecisionOutcomeCreate(
            asin=pick.asin,
            decision=decision,
            decided_at=datetime.utcnow(),
            predicted_roi=pick.roi_percentage,
            predicted_velocity=pick.velocity_score,
            buy_price=pick.buy_price,
            target_sell_price=pick.target_sell_price
        )

        return await self.repository.create_outcome(outcome)

    async def update_actual_outcome(
        self,
        outcome_id: str,
        actual_outcome: str,
        actual_roi: float,
        time_to_sell_days: int
    ):
        """
        Update outcome with actual results (user input)
        """
        return await self.repository.update_outcome(
            outcome_id=outcome_id,
            actual_outcome=actual_outcome,
            actual_roi=actual_roi,
            time_to_sell_days=time_to_sell_days,
            outcome_updated_at=datetime.utcnow()
        )

    async def get_prediction_accuracy(self):
        """
        Calculate prediction accuracy
        """
        outcomes = await self.repository.get_completed_outcomes()

        roi_errors = [abs(o.predicted_roi - o.actual_roi) for o in outcomes if o.actual_roi]
        avg_roi_error = calculate_avg(roi_errors)

        return {
            "total_decisions": len(outcomes),
            "completed_outcomes": len([o for o in outcomes if o.actual_outcome]),
            "avg_roi_prediction_error": avg_roi_error,
            "success_rate": len([o for o in outcomes if o.actual_outcome == 'SOLD']) / len(outcomes)
        }
```

### Background Jobs

#### Daily ASIN Tracking Job
```python
# Cron job: Every day at 2am
@celery.task
async def track_watched_asins():
    """
    Track all ASINs that are in WATCH or TO_BUY status
    """
    picks = await autosourcing_service.get_picks_by_action(['to_buy', 'favorite', 'analyzing'])

    for pick in picks:
        try:
            keepa_data = await keepa_service.get_product(pick.asin)
            await asin_tracking_service.track_asin(pick.asin, keepa_data)
            logger.info(f"Tracked ASIN {pick.asin}")
        except Exception as e:
            logger.error(f"Failed to track {pick.asin}: {e}")

    logger.info(f"Daily tracking complete: {len(picks)} ASINs")
```

### API Endpoints

```python
# GET /api/v1/history/asins/{asin}/trend
@router.get("/{asin}/trend")
async def get_asin_trend(asin: str, days: int = 30):
    return await asin_tracking_service.get_asin_trend(asin, days)

# GET /api/v1/history/runs
@router.get("/runs")
async def get_run_history(limit: int = 20):
    return await run_history_service.get_recent_runs(limit)

# GET /api/v1/history/performance
@router.get("/performance")
async def get_performance_metrics(days: int = 30):
    return await run_history_service.get_performance_metrics(days)

# POST /api/v1/outcomes/{outcome_id}/update
@router.post("/{outcome_id}/update")
async def update_outcome(outcome_id: str, data: OutcomeUpdateSchema):
    return await decision_outcome_service.update_actual_outcome(
        outcome_id, data.actual_outcome, data.actual_roi, data.time_to_sell_days
    )

# GET /api/v1/outcomes/accuracy
@router.get("/accuracy")
async def get_prediction_accuracy():
    return await decision_outcome_service.get_prediction_accuracy()
```

### Acceptance Criteria Phase 8.2
- [ ] Database migrations: 3 nouvelles tables (asin_history, run_history, decision_outcomes)
- [ ] ASIN Tracking Service: Snapshot storage functional
- [ ] Run History Service: Save all AutoSourcing runs
- [ ] Decision Outcome Service: Track decisions et actual results
- [ ] Background job: Daily ASIN tracking (Celery/cron)
- [ ] API endpoints: 5 nouveaux endpoints history
- [ ] Tests: 15+ tests (repository + service layers)

---

## Phase 8.3: Profit & Risk Model

**Timeline:** 1 semaine (5-7 jours)
**Priority:** CRITICAL - Core business logic

### Objectifs
Modeliser risques business reels (dead inventory, storage costs, Amazon competition) et implementer modele 45-60 jours pour recommandations finales.

### Features Detaillees

#### 3.1 Dead Inventory Detection

**Criteres Dead Inventory:**
```python
def is_dead_inventory_risk(asin_data, category):
    """
    Detect products at high risk of becoming dead inventory
    """
    risk_factors = []
    risk_score = 0

    # BSR threshold (category-specific)
    bsr_threshold = get_category_bsr_threshold(category)
    if asin_data.bsr > bsr_threshold:
        risk_factors.append(f"BSR too high: {asin_data.bsr:,} > {bsr_threshold:,}")
        risk_score += 40

    # Slow mover category
    if category in SLOW_MOVER_CATEGORIES:
        risk_factors.append(f"Slow category: {category}")
        risk_score += 20

    # BSR worsening trend
    if asin_data.bsr_trend_30d > 50000:  # BSR increased by 50k+ in 30 days
        risk_factors.append("BSR trend worsening rapidly")
        risk_score += 30

    # High seller count (competition)
    if asin_data.seller_count > 10:
        risk_factors.append(f"High competition: {asin_data.seller_count} sellers")
        risk_score += 10

    return {
        "is_dead_risk": risk_score >= 50,
        "risk_score": risk_score,
        "risk_factors": risk_factors
    }

# Category-specific BSR thresholds
BSR_THRESHOLDS = {
    "Books": 1_000_000,
    "Electronics": 500_000,
    "Health & Personal Care": 300_000,
    "Sports & Outdoors": 400_000
}

SLOW_MOVER_CATEGORIES = [
    "Collectibles",
    "Arts Crafts Sewing",
    "Musical Instruments"
]
```

#### 3.2 Storage Cost Impact (45-60 Day Model)

**Storage Fees Calculation:**
```python
def calculate_storage_costs(dimensions, weight, storage_days):
    """
    Calculate FBA storage fees based on time in warehouse

    Amazon FBA Storage Fees (2025):
    - Standard-size: $0.87/cubic foot (Jan-Sep), $2.40/cubic foot (Oct-Dec)
    - Oversize: $0.56/cubic foot (Jan-Sep), $1.27/cubic foot (Oct-Dec)
    - Long-term storage (365+ days): $6.90/cubic foot or $0.15/unit
    """
    cubic_feet = calculate_cubic_feet(dimensions)

    # Determine period (standard vs peak)
    current_month = datetime.now().month
    is_peak = current_month in [10, 11, 12]  # Oct-Dec

    # Standard vs oversize
    is_oversize = (weight > 20 or cubic_feet > 1)

    if is_oversize:
        monthly_rate = 1.27 if is_peak else 0.56
    else:
        monthly_rate = 2.40 if is_peak else 0.87

    # Calculate monthly cost
    monthly_cost = cubic_feet * monthly_rate

    # Prorate for storage_days
    daily_cost = monthly_cost / 30
    total_cost = daily_cost * storage_days

    # Long-term storage penalty (if > 365 days)
    if storage_days > 365:
        long_term_fee = max(cubic_feet * 6.90, 0.15)
        total_cost += long_term_fee

    return {
        "monthly_storage_cost": round(monthly_cost, 2),
        "storage_cost_45d": round(daily_cost * 45, 2),
        "storage_cost_60d": round(daily_cost * 60, 2),
        "total_cost": round(total_cost, 2),
        "is_peak_season": is_peak
    }
```

**45-60 Day Break-Even Analysis:**
```python
def calculate_breakeven_timeline(buy_price, fees_total, storage_daily_cost, target_roi):
    """
    Calculate max days before break-even ROI drops below target
    """
    required_profit = buy_price * (target_roi / 100)
    required_sell_price = buy_price + fees_total + required_profit

    # Calculate break-even days
    max_storage_cost_allowed = required_profit * 0.3  # 30% of profit max
    breakeven_days = max_storage_cost_allowed / storage_daily_cost

    return {
        "required_sell_price": round(required_sell_price, 2),
        "max_storage_cost_allowed": round(max_storage_cost_allowed, 2),
        "breakeven_days": round(breakeven_days, 0),
        "recommendation": "BUY" if breakeven_days > 45 else "SKIP"
    }
```

#### 3.3 Risk Scoring Algorithm

**Comprehensive Risk Model:**
```python
def calculate_risk_score(asin_data, analytics, category):
    """
    Calculate overall risk score (0-100, lower is better)
    """
    risk_components = {}

    # 1. Dead Inventory Risk (35% weight)
    dead_risk = is_dead_inventory_risk(asin_data, category)
    risk_components['dead_inventory'] = dead_risk['risk_score'] * 0.35

    # 2. Competition Risk (25% weight)
    competition_risk = 0
    if analytics['competition_score'] < 30:  # High competition
        competition_risk = 70
    elif analytics['competition_score'] < 50:
        competition_risk = 40
    else:
        competition_risk = 10
    risk_components['competition'] = competition_risk * 0.25

    # 3. Amazon Presence Risk (20% weight)
    amazon_risk = 80 if asin_data.amazon_on_listing else 0
    risk_components['amazon_presence'] = amazon_risk * 0.20

    # 4. Price Stability Risk (10% weight)
    stability_risk = 100 - analytics['price_stability_score']
    risk_components['price_stability'] = stability_risk * 0.10

    # 5. Category Risk (10% weight)
    category_risk = CATEGORY_RISK_FACTORS.get(category, 30)
    risk_components['category'] = category_risk * 0.10

    # Total risk score
    total_risk = sum(risk_components.values())

    return {
        "total_risk_score": round(total_risk, 2),
        "risk_level": get_risk_level(total_risk),
        "components": risk_components,
        "risk_factors": identify_top_risks(risk_components)
    }

def get_risk_level(risk_score):
    if risk_score < 25:
        return "LOW"
    elif risk_score < 50:
        return "MODERATE"
    elif risk_score < 75:
        return "HIGH"
    else:
        return "CRITICAL"

CATEGORY_RISK_FACTORS = {
    "Books": 20,  # Low risk
    "Electronics": 60,  # High risk (returns, damages)
    "Collectibles": 70,  # Very high risk (slow movers)
    "Health & Personal Care": 30,  # Moderate risk
}
```

#### 3.4 Final Recommendation Engine

**Decision Matrix:**
```python
def generate_final_recommendation(asin_data, analytics, risk_analysis, breakeven):
    """
    Final buy/skip recommendation based on all factors
    """
    roi_net = analytics['roi_net']
    velocity_score = analytics['velocity_score_advanced']
    risk_score = risk_analysis['total_risk_score']
    time_to_sell_estimate = estimate_time_to_sell(velocity_score, asin_data.bsr)

    # Decision criteria
    criteria = {
        "roi_sufficient": roi_net >= 30,
        "velocity_good": velocity_score >= 70,
        "risk_acceptable": risk_score < 50,
        "time_to_sell_ok": time_to_sell_estimate <= 45,
        "amazon_not_present": not asin_data.amazon_on_listing,
        "breakeven_positive": breakeven['recommendation'] == "BUY"
    }

    # Recommendation logic
    passed_criteria = sum(criteria.values())

    if passed_criteria >= 5:
        recommendation = "STRONG_BUY"
        color = "green"
        reason = "High profit, low risk, fast velocity"
    elif passed_criteria >= 4:
        recommendation = "BUY"
        color = "blue"
        reason = "Good opportunity with acceptable risk"
    elif passed_criteria >= 3:
        recommendation = "CONSIDER"
        color = "yellow"
        reason = "Moderate opportunity, evaluate carefully"
    elif passed_criteria >= 2:
        recommendation = "WATCH"
        color = "orange"
        reason = "Monitor for price/competition changes"
    else:
        recommendation = "SKIP"
        color = "red"
        reason = "High risk or insufficient profit potential"

    # Special overrides
    if asin_data.amazon_on_listing and asin_data.amazon_has_buybox:
        recommendation = "AVOID"
        reason = "Amazon owns Buy Box - too risky"

    if risk_analysis['risk_level'] == "CRITICAL":
        recommendation = "AVOID"
        reason = f"Critical risk factors: {', '.join(risk_analysis['risk_factors'])}"

    return {
        "recommendation": recommendation,
        "confidence": calculate_confidence(criteria),
        "reason": reason,
        "color": color,
        "criteria_passed": passed_criteria,
        "criteria_details": criteria,
        "estimated_time_to_sell": time_to_sell_estimate,
        "breakeven_days": breakeven['breakeven_days']
    }

def estimate_time_to_sell(velocity_score, bsr):
    """
    Estimate days to sell based on velocity and BSR
    """
    if velocity_score >= 80:
        return 15  # Fast mover
    elif velocity_score >= 60:
        return 30
    elif velocity_score >= 40:
        return 60
    else:
        return 90  # Slow mover
```

### API Endpoints

```python
# POST /api/v1/risk/analyze
@router.post("/analyze")
async def analyze_risk(asin: str):
    asin_data = await keepa_service.get_product(asin)
    analytics = await analytics_service.get_advanced_analytics(asin)
    risk_analysis = await risk_service.calculate_risk_score(asin_data, analytics)

    return {
        "asin": asin,
        "risk_analysis": risk_analysis,
        "dead_inventory_risk": is_dead_inventory_risk(asin_data),
        "storage_costs": calculate_storage_costs(asin_data.dimensions, asin_data.weight, 45)
    }

# POST /api/v1/risk/recommendation
@router.post("/recommendation")
async def get_recommendation(asin: str):
    asin_data = await keepa_service.get_product(asin)
    analytics = await analytics_service.get_advanced_analytics(asin)
    risk_analysis = await risk_service.calculate_risk_score(asin_data, analytics)
    breakeven = calculate_breakeven_timeline(...)

    recommendation = generate_final_recommendation(asin_data, analytics, risk_analysis, breakeven)

    return {
        "asin": asin,
        "recommendation": recommendation,
        "risk_score": risk_analysis['total_risk_score'],
        "roi_net": analytics['roi_net'],
        "velocity_score": analytics['velocity_score_advanced']
    }
```

### Acceptance Criteria Phase 8.3
- [ ] Dead Inventory Detection: BSR thresholds, category risk factors
- [ ] Storage Cost Calculator: 45/60 day model with peak season
- [ ] Break-Even Analysis: Timeline calculation functional
- [ ] Risk Scoring Algorithm: 5 risk components weighted
- [ ] Recommendation Engine: 5-tier system (STRONG_BUY → AVOID)
- [ ] API endpoints: `/risk/analyze`, `/risk/recommendation`
- [ ] Tests: 20+ scenarios (edge cases, Amazon presence, high risk)
- [ ] Documentation: Risk model documented avec decision matrix

---

## Phase 8.4: Decision UI

**Timeline:** 1 semaine (5-7 jours)
**Priority:** HIGH - User-facing interface

### Objectifs
Interface visuelle complete pour visualiser scores, risques, financials, et recommandations afin de prendre decisions eclairees.

### Components Architecture

```
DecisionDashboard/
├── ProductDecisionCard.tsx       # Main card component
├── ScorePanel.tsx                # Overall score + breakdown
├── RiskPanel.tsx                 # Risk assessment display
├── FinancialPanel.tsx            # Pricing + fees breakdown
├── CompetitionPanel.tsx          # Seller analysis
├── HistoricalTrendsChart.tsx    # BSR/Price trends charts
├── RecommendationBanner.tsx     # Final recommendation
└── ActionButtons.tsx             # Buy/Watch/Skip actions
```

### Component Specifications

#### ProductDecisionCard.tsx
```typescript
interface ProductDecisionCardProps {
  asin: string;
  analytics: AdvancedAnalytics;
  riskAnalysis: RiskAnalysis;
  recommendation: Recommendation;
  historicalData: HistoricalData;
}

const ProductDecisionCard: React.FC<ProductDecisionCardProps> = ({
  asin,
  analytics,
  riskAnalysis,
  recommendation,
  historicalData
}) => {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl">
      {/* Header */}
      <ProductHeader
        asin={asin}
        title={analytics.title}
        imageUrl={analytics.imageUrl}
        category={analytics.category}
      />

      {/* Score Section */}
      <ScorePanel
        overallScore={analytics.overall_score}
        breakdown={{
          roi: analytics.roi_net,
          velocity: analytics.velocity_score_advanced,
          stability: analytics.price_stability_score,
          confidence: recommendation.confidence
        }}
      />

      {/* Risk Assessment */}
      <RiskPanel
        riskScore={riskAnalysis.total_risk_score}
        riskLevel={riskAnalysis.risk_level}
        riskFactors={riskAnalysis.risk_factors}
        amazonPresent={analytics.amazon_on_listing}
        deadInventoryRisk={riskAnalysis.dead_inventory_risk}
      />

      {/* Financial Details */}
      <FinancialPanel
        buyPrice={analytics.buy_price}
        targetSellPrice={analytics.target_sell_price}
        fees={analytics.fees_breakdown}
        netProfit={analytics.net_profit}
        roiNet={analytics.roi_net}
        storageCosts={analytics.storage_costs}
        breakEvenDays={analytics.breakeven_days}
      />

      {/* Competition Analysis */}
      <CompetitionPanel
        totalSellers={analytics.seller_count}
        fbaSellers={analytics.fba_seller_count}
        fbaRatio={analytics.fba_ratio}
        amazonPresent={analytics.amazon_on_listing}
        competitionScore={analytics.competition_score}
      />

      {/* Historical Trends */}
      <HistoricalTrendsChart
        bsrHistory={historicalData.bsr_history}
        priceHistory={historicalData.price_history}
        sellerCountHistory={historicalData.seller_count_history}
      />

      {/* Recommendation */}
      <RecommendationBanner
        recommendation={recommendation.recommendation}
        reason={recommendation.reason}
        color={recommendation.color}
        estimatedTimeToSell={recommendation.estimated_time_to_sell}
      />

      {/* Action Buttons */}
      <ActionButtons
        onBuy={() => handleAction('to_buy')}
        onWatch={() => handleAction('favorite')}
        onSkip={() => handleAction('ignored')}
      />
    </div>
  );
};
```

#### ScorePanel.tsx
```typescript
const ScorePanel: React.FC<ScorePanelProps> = ({ overallScore, breakdown }) => {
  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-4">Score Analysis</h3>

      {/* Overall Score Gauge */}
      <div className="flex items-center justify-center mb-6">
        <CircularProgress
          value={overallScore}
          size={120}
          strokeWidth={10}
          color={getScoreColor(overallScore)}
        />
        <div className="ml-4">
          <div className="text-3xl font-bold">{overallScore}</div>
          <div className="text-gray-600">{getScoreLabel(overallScore)}</div>
        </div>
      </div>

      {/* Score Breakdown */}
      <div className="grid grid-cols-2 gap-4">
        <ScoreBar label="ROI" value={breakdown.roi} max={100} color="green" />
        <ScoreBar label="Velocity" value={breakdown.velocity} max={100} color="blue" />
        <ScoreBar label="Stability" value={breakdown.stability} max={100} color="purple" />
        <ScoreBar label="Confidence" value={breakdown.confidence} max={100} color="gray" />
      </div>
    </div>
  );
};

const ScoreBar: React.FC<ScoreBarProps> = ({ label, value, max, color }) => {
  const percentage = (value / max) * 100;
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-sm text-gray-600">{value}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`bg-${color}-500 h-2 rounded-full`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
```

#### RiskPanel.tsx
```typescript
const RiskPanel: React.FC<RiskPanelProps> = ({
  riskScore,
  riskLevel,
  riskFactors,
  amazonPresent,
  deadInventoryRisk
}) => {
  return (
    <div className="mb-6 p-4 border rounded-lg">
      <h3 className="text-lg font-semibold mb-4">Risk Assessment</h3>

      {/* Risk Score Badge */}
      <div className="flex items-center mb-4">
        <RiskBadge level={riskLevel} score={riskScore} />
        <div className="ml-4">
          <div className="text-sm text-gray-600">Risk Score</div>
          <div className="text-2xl font-bold">{riskScore}/100</div>
        </div>
      </div>

      {/* Critical Warnings */}
      {amazonPresent && (
        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center">
            <AlertCircle className="text-red-600 mr-2" size={20} />
            <span className="text-red-700 font-medium">
              Amazon on listing - High competition risk
            </span>
          </div>
        </div>
      )}

      {deadInventoryRisk && (
        <div className="mb-3 p-3 bg-orange-50 border border-orange-200 rounded-md">
          <div className="flex items-center">
            <AlertTriangle className="text-orange-600 mr-2" size={20} />
            <span className="text-orange-700 font-medium">
              Dead inventory risk detected
            </span>
          </div>
        </div>
      )}

      {/* Risk Factors List */}
      <div>
        <div className="text-sm font-medium mb-2">Risk Factors:</div>
        <ul className="space-y-1">
          {riskFactors.map((factor, idx) => (
            <li key={idx} className="flex items-start text-sm text-gray-700">
              <CheckCircle className="text-gray-400 mr-2 mt-0.5" size={16} />
              {factor}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
```

#### FinancialPanel.tsx
```typescript
const FinancialPanel: React.FC<FinancialPanelProps> = ({
  buyPrice,
  targetSellPrice,
  fees,
  netProfit,
  roiNet,
  storageCosts,
  breakEvenDays
}) => {
  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-4">Financial Analysis</h3>

      {/* Pricing Overview */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <PriceCard label="Buy Price" value={buyPrice} color="gray" />
        <PriceCard label="Target Sell" value={targetSellPrice} color="blue" />
        <PriceCard label="Net Profit" value={netProfit} color="green" bold />
      </div>

      {/* ROI Display */}
      <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
        <div className="text-center">
          <div className="text-sm text-gray-600">Net ROI</div>
          <div className="text-3xl font-bold text-green-700">{roiNet}%</div>
        </div>
      </div>

      {/* Fees Breakdown */}
      <div className="mb-4">
        <div className="text-sm font-medium mb-2">Fees Breakdown:</div>
        <div className="space-y-1 text-sm">
          <FeeRow label="Referral Fee (15%)" value={fees.referral} />
          <FeeRow label="FBA Fee" value={fees.fba} />
          <FeeRow label="Prep + Shipping" value={fees.prep + fees.shipping} />
          <FeeRow label="Returns (5%)" value={fees.returns} />
          <FeeRow label="Damages (2%)" value={fees.damages} />
          <div className="pt-2 border-t">
            <FeeRow label="Total Fees" value={fees.total} bold />
          </div>
        </div>
      </div>

      {/* Storage Costs */}
      <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
        <div className="text-sm font-medium mb-2">Storage Costs:</div>
        <div className="text-sm space-y-1">
          <div>45 days: ${storageCosts.cost_45d}</div>
          <div>60 days: ${storageCosts.cost_60d}</div>
          <div className="font-medium">Break-even: {breakEvenDays} days</div>
        </div>
      </div>
    </div>
  );
};
```

#### HistoricalTrendsChart.tsx
```typescript
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';

const HistoricalTrendsChart: React.FC<HistoricalTrendsChartProps> = ({
  bsrHistory,
  priceHistory,
  sellerCountHistory
}) => {
  const chartData = prepareChartData(bsrHistory, priceHistory, sellerCountHistory);

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-4">Historical Trends (90 Days)</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* BSR Trend */}
        <div>
          <div className="text-sm font-medium mb-2">Sales Rank (BSR)</div>
          <LineChart width={300} height={200} data={chartData}>
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="bsr" stroke="#8884d8" />
          </LineChart>
        </div>

        {/* Price Trend */}
        <div>
          <div className="text-sm font-medium mb-2">Price</div>
          <LineChart width={300} height={200} data={chartData}>
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="price" stroke="#82ca9d" />
          </LineChart>
        </div>
      </div>
    </div>
  );
};
```

#### RecommendationBanner.tsx
```typescript
const RecommendationBanner: React.FC<RecommendationBannerProps> = ({
  recommendation,
  reason,
  color,
  estimatedTimeToSell
}) => {
  const bgColor = `bg-${color}-50`;
  const borderColor = `border-${color}-300`;
  const textColor = `text-${color}-800`;

  return (
    <div className={`mb-6 p-4 ${bgColor} border-2 ${borderColor} rounded-lg`}>
      <div className="flex items-center justify-between">
        <div>
          <div className={`text-2xl font-bold ${textColor} mb-1`}>
            {recommendation}
          </div>
          <div className="text-sm text-gray-700">{reason}</div>
          <div className="text-sm text-gray-600 mt-2">
            Estimated time to sell: {estimatedTimeToSell} days
          </div>
        </div>
        <RecommendationIcon recommendation={recommendation} size={48} />
      </div>
    </div>
  );
};
```

#### ActionButtons.tsx
```typescript
const ActionButtons: React.FC<ActionButtonsProps> = ({
  onBuy,
  onWatch,
  onSkip
}) => {
  return (
    <div className="flex gap-3">
      <button
        onClick={onBuy}
        className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
      >
        Add to Buy List
      </button>
      <button
        onClick={onWatch}
        className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
      >
        Watch
      </button>
      <button
        onClick={onSkip}
        className="flex-1 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
      >
        Skip
      </button>
    </div>
  );
};
```

### Integration avec API

```typescript
// hooks/useProductDecision.ts
export const useProductDecision = (asin: string) => {
  const { data: analytics } = useQuery(['analytics', asin], () =>
    fetch(`/api/v1/analytics/advanced/${asin}`).then(r => r.json())
  );

  const { data: riskAnalysis } = useQuery(['risk', asin], () =>
    fetch(`/api/v1/risk/analyze`, {
      method: 'POST',
      body: JSON.stringify({ asin })
    }).then(r => r.json())
  );

  const { data: recommendation } = useQuery(['recommendation', asin], () =>
    fetch(`/api/v1/risk/recommendation`, {
      method: 'POST',
      body: JSON.stringify({ asin })
    }).then(r => r.json())
  );

  const { data: historicalData } = useQuery(['history', asin], () =>
    fetch(`/api/v1/history/asins/${asin}/trend?days=90`).then(r => r.json())
  );

  return {
    analytics,
    riskAnalysis,
    recommendation,
    historicalData,
    isLoading: !analytics || !riskAnalysis || !recommendation
  };
};
```

### Responsive Design

```typescript
// Mobile-first responsive layout
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
  <ScorePanel />
  <RiskPanel />
</div>

// Stacked on mobile, side-by-side on desktop
<div className="flex flex-col md:flex-row gap-4">
  <FinancialPanel />
  <CompetitionPanel />
</div>
```

### Acceptance Criteria Phase 8.4
- [ ] ProductDecisionCard: Main component complete
- [ ] ScorePanel: Overall score + 4 metrics breakdown
- [ ] RiskPanel: Risk score, warnings, factors list
- [ ] FinancialPanel: Pricing, fees breakdown, storage costs
- [ ] CompetitionPanel: Seller analysis display
- [ ] HistoricalTrendsChart: BSR + Price charts (Recharts)
- [ ] RecommendationBanner: 5-tier recommendation display
- [ ] ActionButtons: Buy/Watch/Skip functional
- [ ] Responsive design: Mobile + tablet + desktop
- [ ] E2E tests: User decision flows
- [ ] Documentation: Component usage guide

---

## Global Acceptance Criteria Phase 8.0

### Backend
- [ ] 4 nouveaux services: Analytics, Historical, Risk, Recommendation
- [ ] 3 nouvelles tables database: asin_history, run_history, decision_outcomes
- [ ] 15+ nouveaux API endpoints
- [ ] Background job: Daily ASIN tracking
- [ ] 50+ tests unitaires + integration
- [ ] Performance: <500ms response time

### Frontend
- [ ] 8 nouveaux composants Decision UI
- [ ] Charts integration (Recharts)
- [ ] Responsive design complete
- [ ] React Query integration
- [ ] 10+ E2E tests decision flows

### Documentation
- [ ] API documentation complete (OpenAPI)
- [ ] Risk model documented avec decision matrix
- [ ] Component library documented
- [ ] User guide: How to interpret decision cards

### Deployment
- [ ] Database migrations tested staging + prod
- [ ] Background jobs deployed (Celery/cron)
- [ ] Performance monitoring (Sentry)
- [ ] Rollback plan documented

---

## Timeline Detaille

### Semaine 1 (Phase 8.1)
- Jours 1-2: Advanced Analytics Engine (velocity, price stability)
- Jours 3-4: ROI Net + Competition Analysis
- Jours 5-7: Tests + API endpoints + Documentation

### Semaine 2 (Phase 8.2)
- Jours 1-2: Database schema + migrations
- Jours 3-4: Services implementation (ASIN tracking, Run history)
- Jours 5-7: Background jobs + API endpoints + Tests

### Semaine 3 (Phase 8.3)
- Jours 1-2: Dead inventory + Storage cost model
- Jours 3-4: Risk scoring + Recommendation engine
- Jours 5-7: Tests + API endpoints + Documentation

### Semaine 4 (Phase 8.4)
- Jours 1-3: UI Components (Score, Risk, Financial panels)
- Jours 4-5: Charts + Recommendation banner
- Jours 6-7: Integration + E2E tests + Polish

---

## Metriques Success

### Business Metrics
- Prediction accuracy: >80% ROI predictions within ±10%
- Dead inventory detection: >90% accuracy
- User satisfaction: >4/5 rating decision cards
- Time to decision: <30 seconds per product

### Technical Metrics
- API response time: <500ms (p95)
- Background job: 100% ASIN tracking success rate
- Database: <1s query time historical data
- Frontend: <3s initial load decision card

---

## Risks & Mitigation

### Risk 1: Keepa API Rate Limits
**Mitigation:** Cache historical data aggressively, background jobs rate-limited

### Risk 2: Storage Cost Calculation Accuracy
**Mitigation:** Use official Amazon FBA fee calculator API if available, otherwise conservative estimates

### Risk 3: Prediction Accuracy Low
**Mitigation:** Iterate on model based on actual outcomes tracked in decision_outcomes table

### Risk 4: UI Performance avec Charts
**Mitigation:** Lazy load charts, use React.memo, virtualization pour listes

---

## Post-Phase 8.0

**Phase 9.0:** UI/UX Polish (ancien Phase 8 incorrect)
**Phase 10.0:** Multi-User & Collaboration

---

**Created:** 16 Novembre 2025
**Owner:** Product + Analytics Development
**Status:** Ready to Start Phase 8.1
**Next Action:** Database schema review + Velocity Analytics kickoff
