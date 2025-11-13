-- Script de création des tables AutoSourcing manquantes
-- À exécuter sur la base de données Neon en production

-- Enum pour JobStatus
CREATE TYPE IF NOT EXISTS jobstatus AS ENUM ('pending', 'running', 'success', 'error', 'cancelled');

-- Enum pour ActionStatus
CREATE TYPE IF NOT EXISTS actionstatus AS ENUM ('pending', 'to_buy', 'favorite', 'ignored', 'analyzing');

-- Table saved_profiles
CREATE TABLE IF NOT EXISTS saved_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    discovery_config JSON NOT NULL,
    scoring_config JSON NOT NULL,
    max_results INTEGER NOT NULL DEFAULT 20,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMP WITHOUT TIME ZONE,
    usage_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index sur saved_profiles
CREATE INDEX IF NOT EXISTS idx_saved_profiles_name ON saved_profiles(name);
CREATE INDEX IF NOT EXISTS idx_saved_profiles_active ON saved_profiles(active);
CREATE INDEX IF NOT EXISTS idx_saved_profiles_last_used ON saved_profiles(last_used_at);
CREATE INDEX IF NOT EXISTS idx_saved_profiles_created ON saved_profiles(created_at);

-- Table autosourcing_jobs
CREATE TABLE IF NOT EXISTS autosourcing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_name VARCHAR(100) NOT NULL,
    profile_id UUID REFERENCES saved_profiles(id) ON DELETE SET NULL,
    launched_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    duration_ms INTEGER,
    status jobstatus NOT NULL DEFAULT 'pending',
    total_tested INTEGER NOT NULL DEFAULT 0,
    total_selected INTEGER NOT NULL DEFAULT 0,
    discovery_config JSON NOT NULL,
    scoring_config JSON NOT NULL,
    error_message TEXT,
    error_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index sur autosourcing_jobs
CREATE INDEX IF NOT EXISTS idx_autosourcing_jobs_profile_name ON autosourcing_jobs(profile_name);
CREATE INDEX IF NOT EXISTS idx_autosourcing_jobs_launched_at ON autosourcing_jobs(launched_at);
CREATE INDEX IF NOT EXISTS idx_autosourcing_jobs_status ON autosourcing_jobs(status);

-- Table autosourcing_picks
CREATE TABLE IF NOT EXISTS autosourcing_picks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES autosourcing_jobs(id) ON DELETE CASCADE,
    asin VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    current_price FLOAT,
    estimated_buy_cost FLOAT,
    profit_net FLOAT,
    roi_percentage FLOAT NOT NULL,
    velocity_score INTEGER NOT NULL,
    stability_score INTEGER NOT NULL,
    confidence_score INTEGER NOT NULL,
    overall_rating VARCHAR(20) NOT NULL,
    bsr INTEGER,
    category VARCHAR(100),
    readable_summary TEXT,
    action_status actionstatus NOT NULL DEFAULT 'pending',
    action_taken_at TIMESTAMP WITHOUT TIME ZONE,
    action_notes TEXT,
    is_purchased BOOLEAN NOT NULL DEFAULT FALSE,
    is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
    is_ignored BOOLEAN NOT NULL DEFAULT FALSE,
    analysis_requested BOOLEAN NOT NULL DEFAULT FALSE,
    deep_analysis_data JSON,
    priority_tier VARCHAR(10) NOT NULL DEFAULT 'WATCH',
    tier_reason TEXT,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    scheduler_run_id VARCHAR(50),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index sur autosourcing_picks
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_job_id ON autosourcing_picks(job_id);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_asin ON autosourcing_picks(asin);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_roi ON autosourcing_picks(roi_percentage);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_velocity ON autosourcing_picks(velocity_score);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_stability ON autosourcing_picks(stability_score);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_confidence ON autosourcing_picks(confidence_score);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_overall_rating ON autosourcing_picks(overall_rating);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_action_status ON autosourcing_picks(action_status);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_is_purchased ON autosourcing_picks(is_purchased);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_is_favorite ON autosourcing_picks(is_favorite);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_is_ignored ON autosourcing_picks(is_ignored);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_priority_tier ON autosourcing_picks(priority_tier);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_is_featured ON autosourcing_picks(is_featured);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_scheduler_run_id ON autosourcing_picks(scheduler_run_id);
CREATE INDEX IF NOT EXISTS idx_autosourcing_picks_created_at ON autosourcing_picks(created_at);

-- Insérer les profils par défaut
INSERT INTO saved_profiles (name, description, discovery_config, scoring_config, max_results)
VALUES
    ('Textbooks Conservateur',
     'Recherche de manuels scolaires avec ROI élevé et faible risque',
     '{"categories": ["Books", "Textbooks"], "bsr_range": [1000, 25000], "price_range": [30, 300], "availability": "amazon"}',
     '{"roi_min": 40, "velocity_min": 70, "stability_min": 80, "confidence_min": 75, "rating_required": "EXCELLENT"}',
     15),
    ('Electronics Opportunity',
     'Scanner électronique avec profit rapide',
     '{"categories": ["Electronics"], "bsr_range": [500, 50000], "price_range": [20, 200], "discount_min": 25}',
     '{"roi_min": 25, "velocity_min": 80, "stability_min": 60, "confidence_min": 70, "rating_required": "GOOD"}',
     25),
    ('Niche Explorer',
     'Découverte de niches spécialisées peu concurrencées',
     '{"categories": ["Books", "Professional", "Medical"], "bsr_range": [5000, 100000], "price_range": [40, 500], "availability": "amazon"}',
     '{"roi_min": 35, "velocity_min": 60, "stability_min": 85, "confidence_min": 80, "rating_required": "EXCELLENT"}',
     10)
ON CONFLICT (name) DO NOTHING;  -- Éviter les doublons si déjà créés

-- Ajouter à alembic_version pour éviter conflits
-- NOTE: Cette ligne est commentée car elle doit être exécutée séparément si nécessaire
-- INSERT INTO alembic_version (version_num) VALUES ('autosourcing_tables_manual_2025') ON CONFLICT DO NOTHING;