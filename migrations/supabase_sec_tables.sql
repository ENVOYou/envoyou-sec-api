-- Envoyou SEC API - Supabase Table Migrations
-- Add SEC-specific tables to existing Supabase database

-- 1. Audit Trail table for SEC compliance
CREATE TABLE IF NOT EXISTS audit_trail (
    id SERIAL PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL,
    calculation_version VARCHAR(50) NOT NULL,
    company_cik VARCHAR(100),
    inputs JSONB,
    factors JSONB,
    source_urls TEXT[],
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Company Facility Mapping table
CREATE TABLE IF NOT EXISTS company_facility_map (
    id SERIAL PRIMARY KEY,
    company VARCHAR(255) NOT NULL UNIQUE,
    facility_id VARCHAR(100) NOT NULL,
    facility_name VARCHAR(255),
    state VARCHAR(10),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Emissions Calculations table (for caching and history)
CREATE TABLE IF NOT EXISTS emissions_calculations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    company VARCHAR(255) NOT NULL,
    calculation_data JSONB NOT NULL,
    result JSONB NOT NULL,
    version VARCHAR(50) DEFAULT '0.1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. SEC Export Packages table (track generated packages)
CREATE TABLE IF NOT EXISTS sec_export_packages (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    company VARCHAR(255) NOT NULL,
    package_data JSONB NOT NULL,
    file_url TEXT,
    file_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_audit_trail_company ON audit_trail(company_cik);
CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp ON audit_trail(timestamp);
CREATE INDEX IF NOT EXISTS idx_company_facility_map_company ON company_facility_map(company);
CREATE INDEX IF NOT EXISTS idx_emissions_calculations_user ON emissions_calculations(user_id);
CREATE INDEX IF NOT EXISTS idx_emissions_calculations_company ON emissions_calculations(company);
CREATE INDEX IF NOT EXISTS idx_sec_export_packages_user ON sec_export_packages(user_id);

-- Add updated_at trigger function if not exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
DROP TRIGGER IF EXISTS update_audit_trail_updated_at ON audit_trail;
CREATE TRIGGER update_audit_trail_updated_at
    BEFORE UPDATE ON audit_trail
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_company_facility_map_updated_at ON company_facility_map;
CREATE TRIGGER update_company_facility_map_updated_at
    BEFORE UPDATE ON company_facility_map
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_emissions_calculations_updated_at ON emissions_calculations;
CREATE TRIGGER update_emissions_calculations_updated_at
    BEFORE UPDATE ON emissions_calculations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE audit_trail ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_facility_map ENABLE ROW LEVEL SECURITY;
ALTER TABLE emissions_calculations ENABLE ROW LEVEL SECURITY;
ALTER TABLE sec_export_packages ENABLE ROW LEVEL SECURITY;

-- Policies for audit_trail (admin only)
CREATE POLICY "Admin can view audit_trail" ON audit_trail
    FOR SELECT USING (
        auth.jwt() ->> 'email' IN (
            'admin@envoyou.com', 'hello@envoyou.com'
        )
    );

CREATE POLICY "Admin can insert audit_trail" ON audit_trail
    FOR INSERT WITH CHECK (
        auth.jwt() ->> 'email' IN (
            'admin@envoyou.com', 'hello@envoyou.com'
        )
    );

-- Policies for company_facility_map (admin only)
CREATE POLICY "Admin can manage company_facility_map" ON company_facility_map
    FOR ALL USING (
        auth.jwt() ->> 'email' IN (
            'admin@envoyou.com', 'hello@envoyou.com'
        )
    );

-- Policies for emissions_calculations (users can manage their own)
CREATE POLICY "Users can view own emissions_calculations" ON emissions_calculations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own emissions_calculations" ON emissions_calculations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own emissions_calculations" ON emissions_calculations
    FOR UPDATE USING (auth.uid() = user_id);

-- Policies for sec_export_packages (users can manage their own)
CREATE POLICY "Users can view own sec_export_packages" ON sec_export_packages
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own sec_export_packages" ON sec_export_packages
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Insert sample data for testing
INSERT INTO company_facility_map (company, facility_id, facility_name, state, notes) 
VALUES 
    ('Demo Corp', '12345', 'Demo Facility', 'TX', 'Test mapping for demo purposes'),
    ('Example Energy Inc', '67890', 'Example Power Plant', 'CA', 'Sample power plant mapping')
ON CONFLICT (company) DO NOTHING;