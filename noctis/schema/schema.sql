CREATE TABLE IF NOT EXISTS niches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    keywords TEXT NOT NULL,
    status TEXT DEFAULT 'collecting',
    score REAL,
    confidence REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche_id INTEGER REFERENCES niches(id) ON DELETE CASCADE,
    sample_type TEXT NOT NULL,
    query_variant TEXT NOT NULL,
    sort_on TEXT NOT NULL,
    listing_count INTEGER DEFAULT 0,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id INTEGER REFERENCES samples(id) ON DELETE CASCADE,
    etsy_listing_id INTEGER NOT NULL,
    title TEXT,
    price REAL,
    currency TEXT,
    tags TEXT,
    views INTEGER,
    num_favorers INTEGER,
    quantity INTEGER,
    shop_id INTEGER,
    creation_timestamp INTEGER,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS calibrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche_id INTEGER REFERENCES niches(id) ON DELETE CASCADE,
    sample_a_id INTEGER REFERENCES samples(id),
    sample_b_id INTEGER REFERENCES samples(id),
    tag_jaccard REAL,
    price_similarity REAL,
    overlap_score REAL,
    passed BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    flag_type TEXT NOT NULL,
    message TEXT NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS my_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche_id INTEGER REFERENCES niches(id),
    etsy_listing_id INTEGER UNIQUE NOT NULL,
    title TEXT,
    price REAL,
    views INTEGER,
    num_favorers INTEGER,
    quantity INTEGER,
    state TEXT,
    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    etsy_receipt_id INTEGER UNIQUE NOT NULL,
    etsy_listing_id INTEGER,
    my_listing_id INTEGER REFERENCES my_listings(id),
    amount_paid REAL,
    currency TEXT,
    buyer_country TEXT,
    sale_date TIMESTAMP,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    detail TEXT,
    status TEXT DEFAULT 'running',
    api_calls_used INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dream_lab_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    messages TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staged_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES dream_lab_sessions(id) ON DELETE CASCADE,
    idea_text TEXT NOT NULL,
    status TEXT DEFAULT 'staged',
    niche_id INTEGER REFERENCES niches(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
