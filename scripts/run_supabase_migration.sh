#!/bin/bash

# Run Supabase migration for SEC API tables
# Usage: ./scripts/run_supabase_migration.sh

set -e

echo "🗄️  Running Supabase Migration for SEC API Tables"
echo "=================================================="

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ psql is not installed. Please install PostgreSQL client."
    exit 1
fi

# Load environment variables
if [ -f .env.production ]; then
    export $(grep -v '^#' .env.production | xargs)
    echo "✅ Loaded production environment variables"
else
    echo "❌ .env.production file not found"
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set in environment"
    exit 1
fi

echo "🔗 Connecting to Supabase PostgreSQL..."
echo "Database: $(echo $DATABASE_URL | sed 's/.*@//' | sed 's/:.*//')"

# Run migration
echo "📝 Executing migration script..."
psql "$DATABASE_URL" -f migrations/supabase_sec_tables.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration completed successfully!"
    echo ""
    echo "📋 Created tables:"
    echo "  - audit_trail (SEC compliance audit trail)"
    echo "  - company_facility_map (company-facility mapping)"
    echo "  - emissions_calculations (calculation history)"
    echo "  - sec_export_packages (export package tracking)"
    echo ""
    echo "🔐 Row Level Security (RLS) enabled with policies"
    echo "📊 Indexes created for performance"
    echo "🧪 Sample data inserted for testing"
    echo ""
    echo "🚀 Ready for frontend integration!"
else
    echo "❌ Migration failed. Check the error messages above."
    exit 1
fi