-- PostgreSQL initialization script for Easy MCP
-- This script is executed when the PostgreSQL container starts for the first time

-- Create database if not exists (handled by POSTGRES_DB environment variable)
-- CREATE DATABASE IF NOT EXISTS easy_mcp;

-- Set timezone
SET timezone = 'UTC';

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges to the user
GRANT ALL PRIVILEGES ON DATABASE easy_mcp TO easy_mcp;

-- Set default character encoding
ALTER DATABASE easy_mcp SET client_encoding TO 'utf8';
ALTER DATABASE easy_mcp SET default_transaction_isolation TO 'read committed';
ALTER DATABASE easy_mcp SET timezone TO 'UTC';

-- Log initialization
SELECT 'PostgreSQL database initialized for Easy MCP' AS message;
