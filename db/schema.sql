-- Enable foreign key enforcement
PRAGMA foreign_keys = ON;

-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

------------------------------------------------------------
-- TABLE: scrape_runs
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scrape_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK(status IN ('running','success','failed')),
    total_records INTEGER DEFAULT 0,
    error_message TEXT
);

------------------------------------------------------------
-- TABLE: papers
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    abstract TEXT,
    published_at TEXT,
    scraped_at TEXT NOT NULL,
    run_id INTEGER NOT NULL,
    FOREIGN KEY (run_id) REFERENCES scrape_runs(id)
);

------------------------------------------------------------
-- TABLE: authors
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

------------------------------------------------------------
-- TABLE: paper_authors (Junction Table)
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS paper_authors (
    paper_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    PRIMARY KEY (paper_id, author_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id),
    FOREIGN KEY (author_id) REFERENCES authors(id)
);

------------------------------------------------------------
-- INDEXES
------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_papers_published_at
ON papers(published_at);

CREATE INDEX IF NOT EXISTS idx_papers_scraped_at
ON papers(scraped_at);

CREATE INDEX IF NOT EXISTS idx_authors_name
ON authors(name);