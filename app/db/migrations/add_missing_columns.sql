-- SQL script to add missing columns to tables
-- Fix database schema mismatches causing Internal Server Error responses

-- Add invite_token column to invites table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='invites' AND column_name='invite_token'
    ) THEN
        -- Create extension for UUID generation if it doesn't exist
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Add the invite_token column
        ALTER TABLE invites 
        ADD COLUMN invite_token VARCHAR(255) NOT NULL DEFAULT uuid_generate_v4();
        
        -- Create unique constraint
        ALTER TABLE invites 
        ADD CONSTRAINT unique_invite_token UNIQUE (invite_token);
        
        RAISE NOTICE 'Added invite_token column to invites table';
    ELSE
        RAISE NOTICE 'invite_token column already exists in invites table';
    END IF;
END $$;

-- Add time column to appointments table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='appointments' AND column_name='time'
    ) THEN
        -- Add the time column
        ALTER TABLE appointments 
        ADD COLUMN time TIME;
        
        -- Update time values based on scheduled_at
        UPDATE appointments 
        SET time = scheduled_at::time
        WHERE scheduled_at IS NOT NULL;
        
        -- Set time to current time for any NULL values
        UPDATE appointments
        SET time = CURRENT_TIME
        WHERE time IS NULL;
        
        -- Make the column NOT NULL after populating it
        ALTER TABLE appointments
        ALTER COLUMN time SET NOT NULL;
        
        RAISE NOTICE 'Added time column to appointments table';
    ELSE
        RAISE NOTICE 'time column already exists in appointments table';
    END IF;
END $$;

-- Add notes column to patients table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='patients' AND column_name='notes'
    ) THEN
        -- Add the notes column
        ALTER TABLE patients 
        ADD COLUMN notes TEXT;
        
        RAISE NOTICE 'Added notes column to patients table';
    ELSE
        RAISE NOTICE 'notes column already exists in patients table';
    END IF;
END $$;
