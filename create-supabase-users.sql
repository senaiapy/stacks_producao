-- Manual SQL script to create Supabase users
-- Run this directly in PostgreSQL if the migration fails

-- Create roles
CREATE ROLE IF NOT EXISTS anon;
CREATE ROLE IF NOT EXISTS authenticated;
CREATE ROLE IF NOT EXISTS service_role;

-- Create authenticator user for PostgREST
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticator') THEN
    CREATE ROLE authenticator LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
  END IF;
END $$;

-- Create supabase_storage_admin user for Storage API
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'supabase_storage_admin') THEN
    CREATE ROLE supabase_storage_admin LOGIN PASSWORD 'Ma1x1x0x!!Ma1x1x0x!!';
  END IF;
END $$;

-- Grant roles to authenticator
GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT service_role TO authenticator;

-- Create schemas if they don't exist
CREATE SCHEMA IF NOT EXISTS "auth";
CREATE SCHEMA IF NOT EXISTS "storage";
CREATE SCHEMA IF NOT EXISTS "realtime";
CREATE SCHEMA IF NOT EXISTS "_realtime";
CREATE SCHEMA IF NOT EXISTS "_analytics";
CREATE SCHEMA IF NOT EXISTS "_supabase";
CREATE SCHEMA IF NOT EXISTS "graphql";
CREATE SCHEMA IF NOT EXISTS "graphql_public";

-- Grant schema permissions
GRANT ALL ON SCHEMA storage TO supabase_storage_admin;
GRANT USAGE ON SCHEMA public TO authenticator;
GRANT USAGE ON SCHEMA storage TO authenticator;
GRANT USAGE ON SCHEMA graphql_public TO authenticator;

-- Create basic storage tables
CREATE TABLE IF NOT EXISTS storage.buckets (
  id text PRIMARY KEY,
  name text NOT NULL,
  owner uuid,
  created_at timestamptz DEFAULT NOW(),
  updated_at timestamptz DEFAULT NOW(),
  public boolean DEFAULT false
);

CREATE TABLE IF NOT EXISTS storage.objects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  bucket_id text REFERENCES storage.buckets(id),
  name text,
  owner uuid,
  created_at timestamptz DEFAULT NOW(),
  updated_at timestamptz DEFAULT NOW(),
  metadata jsonb
);

-- Set ownership
ALTER TABLE storage.buckets OWNER TO supabase_storage_admin;
ALTER TABLE storage.objects OWNER TO supabase_storage_admin;

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA storage TO supabase_storage_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA storage TO supabase_storage_admin;

-- Grant select permissions for API access
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA storage TO anon, authenticated;

-- Create realtime migration table
CREATE TABLE IF NOT EXISTS _realtime.schema_migrations (
  version bigint PRIMARY KEY,
  inserted_at timestamp DEFAULT NOW()
);

GRANT ALL ON SCHEMA _realtime TO chatwoot_database;
GRANT ALL ON _realtime.schema_migrations TO chatwoot_database;

SELECT 'Supabase users and schemas created successfully!' as result;