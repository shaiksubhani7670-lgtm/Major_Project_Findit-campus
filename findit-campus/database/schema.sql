-- ============================================
-- FindIt Campus — PostgreSQL Database Schema
-- Complete schema with relationships, indexes, and constraints
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- ============================================
-- ENUM TYPES
-- ============================================

CREATE TYPE user_role AS ENUM ('student', 'staff', 'admin');
CREATE TYPE item_category AS ENUM (
    'laptop', 'mobile', 'wallet', 'watch', 'keys', 'id_card',
    'bag', 'bottle', 'books', 'earbuds', 'headphones', 'calculator',
    'power_bank', 'helmet', 'shoes', 'jewelry', 'usb_drive',
    'clothes', 'umbrella', 'other'
);
CREATE TYPE lost_item_status AS ENUM ('active', 'matched', 'claimed', 'recovered', 'closed', 'expired');
CREATE TYPE found_item_status AS ENUM ('stored', 'matched', 'claimed', 'returned', 'unclaimed', 'disposed');
CREATE TYPE match_confidence AS ENUM ('very_high', 'high', 'possible', 'low');
CREATE TYPE match_status AS ENUM ('pending', 'confirmed', 'rejected', 'auto_notified');
CREATE TYPE claim_status AS ENUM ('pending', 'under_review', 'approved', 'rejected', 'collected', 'cancelled');
CREATE TYPE notification_type AS ENUM (
    'match_found', 'match_confirmed', 'claim_submitted', 'claim_approved',
    'claim_rejected', 'claim_collected', 'item_status_update', 'system_alert', 'welcome'
);
CREATE TYPE notification_priority AS ENUM ('low', 'medium', 'high', 'urgent');
CREATE TYPE log_level AS ENUM ('info', 'warning', 'error', 'critical');
CREATE TYPE log_action AS ENUM (
    'user_register', 'user_login', 'user_logout', 'password_reset',
    'lost_item_reported', 'lost_item_updated', 'lost_item_closed',
    'found_item_uploaded', 'found_item_updated',
    'match_generated', 'match_confirmed', 'match_rejected',
    'claim_submitted', 'claim_approved', 'claim_rejected', 'claim_collected',
    'ai_processing', 'ai_error', 'admin_action', 'system_event'
);

-- ============================================
-- USERS TABLE
-- ============================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    role user_role NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    last_login TIMESTAMPTZ,

    -- Student-specific fields
    roll_number VARCHAR(50) UNIQUE,
    department VARCHAR(100),
    year_of_study INTEGER,
    section VARCHAR(10),

    -- Staff-specific fields
    staff_id VARCHAR(50) UNIQUE,
    security_office VARCHAR(200),
    shift VARCHAR(50),

    -- Admin-specific fields
    admin_level VARCHAR(50) DEFAULT 'super',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_roll_number ON users(roll_number) WHERE roll_number IS NOT NULL;
CREATE INDEX idx_users_department ON users(department) WHERE department IS NOT NULL;

-- ============================================
-- LOST ITEMS TABLE
-- ============================================

CREATE TABLE lost_items (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    student_name VARCHAR(150),
    roll_number VARCHAR(50),
    department VARCHAR(100),
    phone_number VARCHAR(20),
    college_email VARCHAR(255),

    -- Item details
    item_name VARCHAR(200) NOT NULL,
    category item_category NOT NULL,
    brand VARCHAR(100),
    primary_color VARCHAR(50),
    secondary_color VARCHAR(50),
    material VARCHAR(100),
    description TEXT NOT NULL,

    -- Location details
    lost_date DATE NOT NULL,
    lost_time TIME,
    building VARCHAR(200),
    floor VARCHAR(50),
    room_number VARCHAR(50),
    exact_location VARCHAR(500),

    -- Additional
    reward VARCHAR(200),
    status lost_item_status DEFAULT 'active' NOT NULL,

    -- AI/ML fields
    description_embedding BYTEA,
    detected_category VARCHAR(100),
    ai_features JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_lost_items_student ON lost_items(student_id);
CREATE INDEX idx_lost_items_category ON lost_items(category);
CREATE INDEX idx_lost_items_status ON lost_items(status);
CREATE INDEX idx_lost_items_building ON lost_items(building) WHERE building IS NOT NULL;
CREATE INDEX idx_lost_items_date ON lost_items(lost_date);
CREATE INDEX idx_lost_items_created ON lost_items(created_at DESC);

-- Full-text search index
CREATE INDEX idx_lost_items_search ON lost_items USING gin(
    to_tsvector('english', item_name || ' ' || COALESCE(description, '') || ' ' || COALESCE(brand, ''))
);

-- ============================================
-- LOST ITEM IMAGES TABLE
-- ============================================

CREATE TABLE lost_item_images (
    id SERIAL PRIMARY KEY,
    lost_item_id INTEGER NOT NULL REFERENCES lost_items(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    cloudinary_public_id VARCHAR(300),
    is_primary BOOLEAN DEFAULT FALSE NOT NULL,
    image_embedding BYTEA,
    detected_objects JSONB,
    detected_colors JSONB,
    ocr_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_lost_images_item ON lost_item_images(lost_item_id);

-- ============================================
-- FOUND ITEMS TABLE
-- ============================================

CREATE TABLE found_items (
    id SERIAL PRIMARY KEY,
    staff_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Item details
    item_name VARCHAR(200) NOT NULL,
    category item_category NOT NULL,
    brand VARCHAR(100),
    detected_color VARCHAR(50),
    manual_color VARCHAR(50),
    material VARCHAR(100),
    description TEXT NOT NULL,

    -- Location details
    found_date DATE NOT NULL,
    found_time TIME,
    building VARCHAR(200),
    floor VARCHAR(50),
    room_number VARCHAR(50),
    exact_location VARCHAR(500),

    -- Storage details
    security_office VARCHAR(200),
    storage_location VARCHAR(200),
    status found_item_status DEFAULT 'stored' NOT NULL,

    -- AI/ML fields
    description_embedding BYTEA,
    detected_category VARCHAR(100),
    ai_features JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_found_items_staff ON found_items(staff_id);
CREATE INDEX idx_found_items_category ON found_items(category);
CREATE INDEX idx_found_items_status ON found_items(status);
CREATE INDEX idx_found_items_building ON found_items(building) WHERE building IS NOT NULL;
CREATE INDEX idx_found_items_created ON found_items(created_at DESC);

-- ============================================
-- FOUND ITEM IMAGES TABLE
-- ============================================

CREATE TABLE found_item_images (
    id SERIAL PRIMARY KEY,
    found_item_id INTEGER NOT NULL REFERENCES found_items(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    cloudinary_public_id VARCHAR(300),
    is_primary BOOLEAN DEFAULT FALSE NOT NULL,
    image_embedding BYTEA,
    detected_objects JSONB,
    detected_colors JSONB,
    ocr_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_found_images_item ON found_item_images(found_item_id);

-- ============================================
-- MATCHES TABLE
-- ============================================

CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    lost_item_id INTEGER NOT NULL REFERENCES lost_items(id) ON DELETE CASCADE,
    found_item_id INTEGER NOT NULL REFERENCES found_items(id) ON DELETE CASCADE,

    -- Confidence
    confidence_score FLOAT NOT NULL,
    confidence_level match_confidence NOT NULL,

    -- Individual scores (0.0 to 1.0)
    image_similarity FLOAT,
    text_similarity FLOAT,
    color_similarity FLOAT,
    brand_similarity FLOAT,
    location_similarity FLOAT,
    date_similarity FLOAT,

    -- Review
    status match_status DEFAULT 'pending' NOT NULL,
    reviewed_by INTEGER REFERENCES users(id),
    review_notes TEXT,
    reviewed_at TIMESTAMPTZ,

    -- Metadata
    match_details JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- One match per lost-found pair
    UNIQUE(lost_item_id, found_item_id)
);

CREATE INDEX idx_matches_lost ON matches(lost_item_id);
CREATE INDEX idx_matches_found ON matches(found_item_id);
CREATE INDEX idx_matches_score ON matches(confidence_score DESC);
CREATE INDEX idx_matches_status ON matches(status);

-- ============================================
-- CLAIMS TABLE
-- ============================================

CREATE TABLE claims (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    lost_item_id INTEGER NOT NULL REFERENCES lost_items(id),
    found_item_id INTEGER NOT NULL REFERENCES found_items(id),

    -- Claim details
    claim_description TEXT,
    proof_images JSONB,
    status claim_status DEFAULT 'pending' NOT NULL,

    -- Verification
    verified_by INTEGER REFERENCES users(id),
    verification_notes TEXT,
    verified_at TIMESTAMPTZ,

    -- Admin approval
    approved_by INTEGER REFERENCES users(id),
    approval_notes TEXT,
    approved_at TIMESTAMPTZ,

    -- Collection
    collected_at TIMESTAMPTZ,
    collection_notes TEXT,

    -- Rejection
    rejection_reason TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_claims_student ON claims(student_id);
CREATE INDEX idx_claims_match ON claims(match_id);
CREATE INDEX idx_claims_status ON claims(status);

-- ============================================
-- NOTIFICATIONS TABLE
-- ============================================

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    title VARCHAR(300) NOT NULL,
    message TEXT NOT NULL,
    type notification_type NOT NULL,
    priority notification_priority DEFAULT 'medium' NOT NULL,

    -- Related entities
    related_item_id INTEGER,
    related_match_id INTEGER,
    related_claim_id INTEGER,

    -- Delivery status
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMPTZ,
    is_email_sent BOOLEAN DEFAULT FALSE NOT NULL,
    email_sent_at TIMESTAMPTZ,

    action_url VARCHAR(500),
    notif_metadata JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- ============================================
-- SYSTEM LOGS TABLE
-- ============================================

CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action log_action NOT NULL,
    level log_level DEFAULT 'info' NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_logs_user ON system_logs(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_logs_action ON system_logs(action);
CREATE INDEX idx_logs_level ON system_logs(level);
CREATE INDEX idx_logs_created ON system_logs(created_at DESC);

-- ============================================
-- AUTO-UPDATE TIMESTAMP TRIGGER
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_lost_items_updated_at
    BEFORE UPDATE ON lost_items FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_found_items_updated_at
    BEFORE UPDATE ON found_items FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_matches_updated_at
    BEFORE UPDATE ON matches FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_claims_updated_at
    BEFORE UPDATE ON claims FOR EACH ROW EXECUTE FUNCTION update_updated_at();
