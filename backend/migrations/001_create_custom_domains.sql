-- Custom domains table
CREATE TABLE IF NOT EXISTS custom_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    domain VARCHAR(255) UNIQUE NOT NULL,
    verification_token VARCHAR(255) NOT NULL,
    verification_method VARCHAR(50) NOT NULL, -- 'dns', 'http', 'file'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'verified', 'active', 'error'
    ssl_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'active', 'error'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Domain verification records
CREATE TABLE IF NOT EXISTS domain_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID REFERENCES custom_domains(id) ON DELETE CASCADE,
    verification_type VARCHAR(50) NOT NULL, -- 'dns', 'http', 'file'
    verification_data TEXT NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Domain health monitoring
CREATE TABLE IF NOT EXISTS domain_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID REFERENCES custom_domains(id) ON DELETE CASCADE,
    status_code INTEGER,
    response_time_ms INTEGER,
    ssl_valid BOOLEAN,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_custom_domains_user_id ON custom_domains(user_id);
CREATE INDEX IF NOT EXISTS idx_custom_domains_workspace_id ON custom_domains(workspace_id);
CREATE INDEX IF NOT EXISTS idx_custom_domains_status ON custom_domains(status);
CREATE INDEX IF NOT EXISTS idx_custom_domains_domain ON custom_domains(domain);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_custom_domains_updated_at 
    BEFORE UPDATE ON custom_domains 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
