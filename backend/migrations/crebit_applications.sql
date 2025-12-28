-- Crebit Applications Table
-- Run this manually on your PostgreSQL database

CREATE TABLE IF NOT EXISTS crebit_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Applicant info
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    
    -- Track selection: 'A' (Cinematic) or 'B' (Motion Graphics)
    track CHAR(1) NOT NULL CHECK (track IN ('A', 'B')),
    
    -- Application status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending: Application received, awaiting payment
    -- paid: Payment completed
    -- cancelled: Cancelled by user/admin
    -- refunded: Refunded
    
    -- Payment info (Phase 2)
    payment_id VARCHAR(100),
    paid_amount INTEGER,
    paid_at TIMESTAMP,
    
    -- Metadata
    cohort VARCHAR(10) DEFAULT '1기',
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_crebit_applications_email ON crebit_applications(email);
CREATE INDEX IF NOT EXISTS idx_crebit_applications_status ON crebit_applications(status);
CREATE INDEX IF NOT EXISTS idx_crebit_applications_created_at ON crebit_applications(created_at);
