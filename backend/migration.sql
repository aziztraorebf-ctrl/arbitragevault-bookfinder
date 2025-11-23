BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> f87fea7f163c

CREATE TABLE users (
    email VARCHAR(255) NOT NULL, 
    password_hash TEXT NOT NULL, 
    first_name VARCHAR(100), 
    last_name VARCHAR(100), 
    role VARCHAR(20) NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    is_verified BOOLEAN NOT NULL, 
    last_login_at TIMESTAMP WITH TIME ZONE, 
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    failed_login_attempts INTEGER NOT NULL, 
    locked_until TIMESTAMP WITH TIME ZONE, 
    verification_token VARCHAR(255), 
    verification_token_expires_at TIMESTAMP WITH TIME ZONE, 
    reset_token VARCHAR(255), 
    reset_token_expires_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE refresh_tokens (
    user_id UUID NOT NULL, 
    token_hash TEXT NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    is_revoked BOOLEAN NOT NULL, 
    revoked_at TIMESTAMP WITH TIME ZONE, 
    ip_address VARCHAR(45), 
    user_agent TEXT, 
    last_used_at TIMESTAMP WITH TIME ZONE, 
    id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_refresh_tokens_token_hash ON refresh_tokens (token_hash);

CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id);

INSERT INTO alembic_version (version_num) VALUES ('f87fea7f163c') RETURNING alembic_version.version_num;

-- Running upgrade f87fea7f163c -> 4a0c777df81d

CREATE TYPE batch_status AS ENUM ('PENDING', 'RUNNING', 'DONE', 'FAILED');

CREATE TABLE batches (
    user_id VARCHAR(36) NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    status batch_status NOT NULL, 
    items_total INTEGER NOT NULL, 
    items_processed INTEGER NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE, 
    finished_at TIMESTAMP WITH TIME ZONE, 
    strategy_snapshot JSON, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_processed_not_exceed_total CHECK (items_processed <= items_total), 
    CONSTRAINT check_items_processed_positive CHECK (items_processed >= 0), 
    CONSTRAINT check_items_total_positive CHECK (items_total >= 0), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_batches_status ON batches (status);

CREATE INDEX ix_batches_user_created ON batches (user_id, created_at);

CREATE TABLE analyses (
    batch_id VARCHAR(36) NOT NULL, 
    isbn_or_asin VARCHAR(20) NOT NULL, 
    buy_price NUMERIC(12, 2) NOT NULL, 
    fees NUMERIC(12, 2) NOT NULL, 
    expected_sale_price NUMERIC(12, 2) NOT NULL, 
    profit NUMERIC(12, 2) NOT NULL, 
    roi_percent NUMERIC(6, 2) NOT NULL, 
    velocity_score NUMERIC(6, 2) NOT NULL, 
    rank_snapshot INTEGER, 
    offers_count INTEGER, 
    raw_keepa JSON, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT check_buy_price_positive CHECK (buy_price >= 0), 
    CONSTRAINT check_sale_price_positive CHECK (expected_sale_price >= 0), 
    CONSTRAINT check_fees_positive CHECK (fees >= 0), 
    CONSTRAINT check_velocity_score_max CHECK (velocity_score <= 100), 
    CONSTRAINT check_velocity_score_min CHECK (velocity_score >= 0), 
    FOREIGN KEY(batch_id) REFERENCES batches (id) ON DELETE CASCADE, 
    CONSTRAINT uq_analysis_batch_isbn UNIQUE (batch_id, isbn_or_asin)
);

CREATE INDEX ix_analyses_batch_id ON analyses (batch_id);

CREATE INDEX ix_analyses_isbn ON analyses (isbn_or_asin);

CREATE INDEX ix_analyses_roi ON analyses (roi_percent);

CREATE INDEX ix_analyses_velocity ON analyses (velocity_score);

UPDATE alembic_version SET version_num='4a0c777df81d' WHERE alembic_version.version_num = 'f87fea7f163c';

-- Running upgrade 4a0c777df81d -> 002_add_composite_indexes

CREATE INDEX idx_analyses_batch_roi ON analyses USING btree (batch_id, roi_percent);

CREATE INDEX idx_analyses_batch_velocity ON analyses USING btree (batch_id, velocity_score);

CREATE INDEX idx_analyses_batch_profit ON analyses USING btree (batch_id, profit);

CREATE INDEX idx_analyses_roi_id ON analyses USING btree (roi_percent, id);

CREATE INDEX idx_analyses_velocity_id ON analyses USING btree (velocity_score, id);

CREATE INDEX idx_analyses_profit_id ON analyses USING btree (profit, id);

UPDATE alembic_version SET version_num='002_add_composite_indexes' WHERE alembic_version.version_num = '4a0c777df81d';

-- Running upgrade 002_add_composite_indexes -> 5e5eed2533e7

CREATE TABLE keepa_products (
    id VARCHAR NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    asin VARCHAR(10) NOT NULL, 
    title TEXT, 
    category VARCHAR(100), 
    brand VARCHAR(200), 
    manufacturer VARCHAR(200), 
    package_height NUMERIC(10, 2), 
    package_length NUMERIC(10, 2), 
    package_width NUMERIC(10, 2), 
    package_weight NUMERIC(10, 3), 
    status VARCHAR(20) NOT NULL, 
    domain INTEGER NOT NULL, 
    original_identifier VARCHAR(20), 
    identifier_type VARCHAR(10), 
    last_keepa_sync TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    UNIQUE (asin)
);

CREATE UNIQUE INDEX ix_keepa_products_asin ON keepa_products (asin);

CREATE TABLE keepa_snapshots (
    id VARCHAR NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    product_id VARCHAR NOT NULL, 
    snapshot_date TIMESTAMP WITH TIME ZONE NOT NULL, 
    data_window_days INTEGER NOT NULL, 
    current_buybox_price NUMERIC(10, 2), 
    current_amazon_price NUMERIC(10, 2), 
    current_fba_price NUMERIC(10, 2), 
    current_fbm_price NUMERIC(10, 2), 
    current_bsr INTEGER, 
    raw_data JSONB, 
    metrics_data JSONB, 
    offers_count INTEGER, 
    buybox_seller_type VARCHAR(20), 
    is_prime_eligible VARCHAR(10), 
    PRIMARY KEY (id), 
    FOREIGN KEY(product_id) REFERENCES keepa_products (id) ON DELETE CASCADE
);

CREATE INDEX ix_keepa_snapshots_product_id ON keepa_snapshots (product_id);

CREATE INDEX ix_keepa_snapshots_snapshot_date ON keepa_snapshots (snapshot_date);

CREATE INDEX ix_keepa_snapshots_current_bsr ON keepa_snapshots (current_bsr);

CREATE TABLE calc_metrics (
    id VARCHAR NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    product_id VARCHAR NOT NULL, 
    snapshot_id VARCHAR, 
    estimated_sell_price NUMERIC(10, 2), 
    estimated_buy_cost NUMERIC(10, 2), 
    amazon_fees_total NUMERIC(10, 2), 
    net_profit NUMERIC(10, 2), 
    roi_percentage NUMERIC(5, 2), 
    margin_percentage NUMERIC(5, 2), 
    referral_fee NUMERIC(8, 2), 
    closing_fee NUMERIC(8, 2), 
    fba_fee NUMERIC(8, 2), 
    inbound_shipping NUMERIC(8, 2), 
    prep_fee NUMERIC(8, 2), 
    target_buy_price NUMERIC(10, 2), 
    breakeven_price NUMERIC(10, 2), 
    velocity_score NUMERIC(5, 2), 
    rank_percentile_30d NUMERIC(5, 2), 
    rank_drops_30d INTEGER, 
    buybox_uptime_30d NUMERIC(5, 2), 
    offers_volatility NUMERIC(5, 2), 
    demand_consistency NUMERIC(5, 2), 
    price_volatility NUMERIC(5, 2), 
    competition_level NUMERIC(5, 2), 
    fee_config_used JSONB, 
    calculation_params JSONB, 
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    calculation_version VARCHAR(10) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(product_id) REFERENCES keepa_products (id) ON DELETE CASCADE, 
    FOREIGN KEY(snapshot_id) REFERENCES keepa_snapshots (id) ON DELETE CASCADE
);

CREATE INDEX ix_calc_metrics_product_id ON calc_metrics (product_id);

CREATE INDEX ix_calc_metrics_snapshot_id ON calc_metrics (snapshot_id);

CREATE INDEX ix_calc_metrics_net_profit ON calc_metrics (net_profit);

CREATE INDEX ix_calc_metrics_roi_percentage ON calc_metrics (roi_percentage);

CREATE INDEX ix_calc_metrics_velocity_score ON calc_metrics (velocity_score);

CREATE TABLE identifier_resolution_log (
    id VARCHAR NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    original_identifier VARCHAR(20) NOT NULL, 
    identifier_type VARCHAR(10) NOT NULL, 
    resolved_asin VARCHAR(10), 
    resolution_status VARCHAR(20) NOT NULL, 
    keepa_product_code INTEGER, 
    keepa_domain INTEGER NOT NULL, 
    error_message TEXT, 
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_identifier_resolution_log_original_identifier ON identifier_resolution_log (original_identifier);

CREATE INDEX ix_identifier_resolution_log_resolved_asin ON identifier_resolution_log (resolved_asin);

UPDATE alembic_version SET version_num='5e5eed2533e7' WHERE alembic_version.version_num = '002_add_composite_indexes';

-- Running upgrade 5e5eed2533e7 -> 2f821440fee5

CREATE TABLE business_config (
    id SERIAL NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    scope VARCHAR(50) NOT NULL, 
    data JSONB NOT NULL, 
    version INTEGER NOT NULL, 
    parent_id INTEGER, 
    description TEXT, 
    is_active BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(parent_id) REFERENCES business_config (id) ON DELETE CASCADE, 
    CONSTRAINT single_global_config CHECK ((scope = 'global' AND id = 1) OR (scope != 'global')), 
    CONSTRAINT valid_scope_format CHECK (scope ~ '^(global|domain:[0-9]+|category:[a-z_]+)$')
);

CREATE INDEX ix_business_config_scope ON business_config (scope);

CREATE INDEX ix_business_config_parent_id ON business_config (parent_id);

CREATE TABLE config_changes (
    id VARCHAR NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    config_id INTEGER NOT NULL, 
    old_config JSONB, 
    new_config JSONB NOT NULL, 
    diff_jsonpatch JSONB NOT NULL, 
    changed_by VARCHAR(100) NOT NULL, 
    change_reason TEXT, 
    change_source VARCHAR(20) NOT NULL, 
    old_version INTEGER, 
    new_version INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(config_id) REFERENCES business_config (id) ON DELETE CASCADE
);

CREATE INDEX ix_config_changes_config_id ON config_changes (config_id);

INSERT INTO business_config (id, scope, data, version, description, is_active, created_at, updated_at)
            VALUES (1, 'global', '{"roi": {"target_pct_default": 30.0, "min_for_buy": 15.0, "excellent_threshold": 50.0, "good_threshold": 30.0, "fair_threshold": 15.0}, "combined_score": {"roi_weight": 0.6, "velocity_weight": 0.4}, "fees": {"buffer_pct_default": 5.0, "books": {"referral_fee_pct": 15.0, "closing_fee": 1.8, "fba_fee_base": 2.5, "fba_fee_per_lb": 0.4, "inbound_shipping": 0.4, "prep_fee": 0.2}}, "velocity": {"fast_threshold": 80.0, "medium_threshold": 60.0, "slow_threshold": 40.0, "benchmarks": {"books": 100000, "media": 50000, "default": 150000}}, "recommendation_rules": [{"label": "STRONG BUY", "min_roi": 30.0, "min_velocity": 70.0, "description": "High profit, fast moving"}, {"label": "BUY", "min_roi": 20.0, "min_velocity": 50.0, "description": "Good opportunity"}, {"label": "CONSIDER", "min_roi": 15.0, "min_velocity": 0.0, "description": "Monitor for better entry"}, {"label": "PASS", "min_roi": 0.0, "min_velocity": 0.0, "description": "Low profit/slow moving"}], "demo_asins": ["B00FLIJJSA", "B08N5WRWNW", "B07FNW9FGJ"], "meta": {"version": "1.0.0", "created_by": "migration_seed", "description": "Default business configuration seeded from migration"}}', 1, 'Global business configuration', true, now(), now());

UPDATE alembic_version SET version_num='2f821440fee5' WHERE alembic_version.version_num = '5e5eed2533e7';

-- Running upgrade 2f821440fee5 -> add_discovery_cache

CREATE TABLE product_discovery_cache (
    cache_key VARCHAR(255) NOT NULL, 
    asins JSON NOT NULL, 
    filters_applied JSON, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    hit_count INTEGER NOT NULL, 
    PRIMARY KEY (cache_key)
);

COMMENT ON COLUMN product_discovery_cache.asins IS 'Liste des ASINs découverts';

COMMENT ON COLUMN product_discovery_cache.filters_applied IS 'Filtres utilisés pour la recherche';

COMMENT ON COLUMN product_discovery_cache.expires_at IS 'TTL 24h par défaut';

COMMENT ON COLUMN product_discovery_cache.hit_count IS 'Nombre de fois que ce cache a été utilisé';

CREATE INDEX idx_discovery_expires_at ON product_discovery_cache (expires_at);

CREATE INDEX idx_discovery_created_at ON product_discovery_cache (created_at);

CREATE TABLE product_scoring_cache (
    cache_key VARCHAR(255) NOT NULL, 
    asin VARCHAR(20) NOT NULL, 
    roi_percent FLOAT NOT NULL, 
    velocity_score FLOAT NOT NULL, 
    recommendation VARCHAR(50) NOT NULL, 
    title VARCHAR(500), 
    price FLOAT, 
    bsr INTEGER, 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    hit_count INTEGER NOT NULL, 
    PRIMARY KEY (cache_key)
);

COMMENT ON COLUMN product_scoring_cache.recommendation IS 'STRONG_BUY, BUY, CONSIDER, SKIP';

COMMENT ON COLUMN product_scoring_cache.expires_at IS 'TTL 6h par défaut';

CREATE INDEX idx_scoring_expires_at ON product_scoring_cache (expires_at);

CREATE INDEX idx_scoring_asin ON product_scoring_cache (asin);

CREATE INDEX idx_scoring_roi ON product_scoring_cache (roi_percent);

CREATE INDEX idx_scoring_velocity ON product_scoring_cache (velocity_score);

CREATE TABLE search_history (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36), 
    search_type VARCHAR(50) NOT NULL, 
    filters JSON NOT NULL, 
    results_count INTEGER NOT NULL, 
    source VARCHAR(50), 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

COMMENT ON COLUMN search_history.user_id IS 'Future auth - actuellement NULL';

COMMENT ON COLUMN search_history.search_type IS 'discovery, scoring, autosourcing';

COMMENT ON COLUMN search_history.filters IS 'Filtres appliqués';

COMMENT ON COLUMN search_history.source IS 'frontend, api, manual';

CREATE INDEX idx_history_created_at ON search_history (created_at);

CREATE INDEX idx_history_user_id ON search_history (user_id);

CREATE INDEX idx_history_search_type ON search_history (search_type);

UPDATE alembic_version SET version_num='add_discovery_cache' WHERE alembic_version.version_num = '2f821440fee5';

-- Running upgrade add_discovery_cache -> 45d219e45e5a

ALTER TABLE product_discovery_cache DROP COLUMN filters_applied;

ALTER TABLE product_discovery_cache ADD COLUMN domain INTEGER DEFAULT '1' NOT NULL;

ALTER TABLE product_discovery_cache ADD COLUMN category INTEGER;

ALTER TABLE product_discovery_cache ADD COLUMN bsr_min INTEGER;

ALTER TABLE product_discovery_cache ADD COLUMN bsr_max INTEGER;

ALTER TABLE product_discovery_cache ADD COLUMN price_min FLOAT;

ALTER TABLE product_discovery_cache ADD COLUMN price_max FLOAT;

ALTER TABLE product_discovery_cache ADD COLUMN count INTEGER DEFAULT '0' NOT NULL;

ALTER TABLE product_discovery_cache ALTER COLUMN domain DROP DEFAULT;

ALTER TABLE product_discovery_cache ALTER COLUMN count DROP DEFAULT;

UPDATE alembic_version SET version_num='45d219e45e5a' WHERE alembic_version.version_num = 'add_discovery_cache';

-- Running upgrade 45d219e45e5a -> fix_scoring_cache_pk

DROP INDEX idx_scoring_expires_at;

DROP INDEX idx_scoring_asin;

DROP INDEX idx_scoring_roi;

DROP INDEX idx_scoring_velocity;

DROP TABLE product_scoring_cache;

CREATE TABLE product_scoring_cache (
    id SERIAL NOT NULL, 
    asin VARCHAR(20) NOT NULL, 
    title TEXT, 
    price FLOAT NOT NULL, 
    bsr INTEGER NOT NULL, 
    roi_percent FLOAT NOT NULL, 
    velocity_score FLOAT NOT NULL, 
    recommendation VARCHAR(50) NOT NULL, 
    keepa_data JSON, 
    config_hash VARCHAR(64), 
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
    analysis_version VARCHAR(20) DEFAULT '1.0' NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_scoring_cache_asin_expiry ON product_scoring_cache (asin, expires_at);

CREATE INDEX idx_scoring_cache_recommendation ON product_scoring_cache (recommendation);

CREATE INDEX idx_scoring_cache_roi ON product_scoring_cache (roi_percent);

UPDATE alembic_version SET version_num='fix_scoring_cache_pk' WHERE alembic_version.version_num = '45d219e45e5a';

-- Running upgrade fix_scoring_cache_pk -> 008835e8f328

CREATE TABLE saved_niches (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    niche_name VARCHAR(255) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    category_id INTEGER, 
    category_name VARCHAR(255), 
    filters JSONB DEFAULT '{}' NOT NULL, 
    last_score FLOAT, 
    description TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_saved_niches_user_id ON saved_niches (user_id);

CREATE INDEX ix_saved_niches_niche_name ON saved_niches (niche_name);

COMMENT ON COLUMN saved_niches.niche_name IS 'User-defined name for the niche';

COMMENT ON COLUMN saved_niches.user_id IS 'ID of the user who saved this niche';

COMMENT ON COLUMN saved_niches.category_id IS 'Keepa category ID used for niche discovery';

COMMENT ON COLUMN saved_niches.category_name IS 'Human-readable category name';

COMMENT ON COLUMN saved_niches.filters IS 'Complete analysis parameters';

COMMENT ON COLUMN saved_niches.last_score IS 'Last calculated niche score';

COMMENT ON COLUMN saved_niches.description IS 'Optional user notes';

CREATE INDEX ix_saved_niches_user_created ON saved_niches USING btree (user_id, created_at);

UPDATE alembic_version SET version_num='008835e8f328' WHERE alembic_version.version_num = 'fix_scoring_cache_pk';

-- Running upgrade 008835e8f328 -> phase_8_0_analytics

CREATE TABLE asin_history (
    id UUID NOT NULL, 
    asin VARCHAR(10) NOT NULL, 
    tracked_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    price NUMERIC(10, 2), 
    lowest_fba_price NUMERIC(10, 2), 
    bsr INTEGER, 
    seller_count INTEGER, 
    amazon_on_listing BOOLEAN, 
    fba_seller_count INTEGER, 
    extra_data JSON, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_asin_history_asin_tracked ON asin_history (asin, tracked_at);

CREATE INDEX idx_asin_history_tracked_at ON asin_history (tracked_at);

CREATE INDEX ix_asin_history_asin ON asin_history (asin);

CREATE TABLE run_history (
    id UUID NOT NULL, 
    job_id UUID NOT NULL, 
    config_snapshot JSON NOT NULL, 
    total_products_discovered INTEGER NOT NULL, 
    total_picks_generated INTEGER NOT NULL, 
    success_rate NUMERIC(5, 2), 
    tokens_consumed INTEGER DEFAULT '0' NOT NULL, 
    execution_time_seconds FLOAT, 
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_run_history_job_id ON run_history (job_id);

CREATE INDEX idx_run_history_executed_at ON run_history (executed_at);

CREATE TABLE decision_outcomes (
    id UUID NOT NULL, 
    asin VARCHAR(10) NOT NULL, 
    decision VARCHAR(20) NOT NULL, 
    predicted_roi NUMERIC(5, 2), 
    predicted_velocity NUMERIC(5, 2), 
    predicted_risk_score NUMERIC(5, 2), 
    actual_outcome VARCHAR(20), 
    actual_roi NUMERIC(5, 2), 
    time_to_sell_days INTEGER, 
    outcome_date TIMESTAMP WITH TIME ZONE, 
    notes TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_decision_outcome_asin ON decision_outcomes (asin);

CREATE INDEX idx_decision_outcome_decision ON decision_outcomes (decision);

CREATE INDEX idx_decision_outcome_created_at ON decision_outcomes (created_at);

UPDATE alembic_version SET version_num='phase_8_0_analytics' WHERE alembic_version.version_num = '008835e8f328';

COMMIT;

