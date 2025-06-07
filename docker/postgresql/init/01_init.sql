-- PostgreSQL initialization script for Genascope
-- This script sets up the database extensions and creates initial schema

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "hstore";

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create enum types for better type safety
CREATE TYPE user_role AS ENUM ('patient', 'clinician', 'admin', 'super_admin', 'lab_tech');
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'invited', 'suspended');
CREATE TYPE account_status AS ENUM ('active', 'inactive', 'suspended');
CREATE TYPE patient_status AS ENUM ('active', 'inactive', 'archived');
CREATE TYPE invite_status AS ENUM ('pending', 'completed', 'expired');
CREATE TYPE chat_session_status AS ENUM ('in_progress', 'completed', 'abandoned');
CREATE TYPE appointment_type AS ENUM ('virtual', 'in_person');
CREATE TYPE appointment_status AS ENUM ('scheduled', 'completed', 'cancelled', 'no_show');
CREATE TYPE lab_order_status AS ENUM ('ordered', 'processing', 'completed', 'cancelled');
CREATE TYPE lab_result_status AS ENUM ('pending', 'available', 'reviewed');

-- Log the initialization
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL initialization completed for Genascope database';
END $$;
