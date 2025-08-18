-- Database initialization script
-- This file is executed when the PostgreSQL container starts for the first time

-- Create extensions that we'll need
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone to UTC
SET timezone = 'UTC';

-- Basic setup is handled by Alembic migrations
-- This file exists for future custom initialization needs