import sqlite3
from config import DB_PATH
from datetime import datetime


# Signular DB entry point for enture project
def get_connection():
    """
    Creates and returns a new SQLite connection
    with foreign key enforcement enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_scrape_run():
    """
    Creates a new scrape run with status='running'
    Returns the created run_id.
    """
    conn = get_connection()
    cursor = conn.cursor()

    started_at = datetime.utcnow().isoformat()

    cursor.execute(
        """
        INSERT INTO scrape_runs (started_at, status)
        VALUES (?, ?)
    """,
        (started_at, "running"),
    )

    conn.commit()

    run_id = cursor.lastrowid
    conn.close()

    return run_id


def update_scrape_run(run_id, status, total_records=0, error_message=None):
    """
    Updates an existing scrape run with final status.
    """
    from datetime import datetime

    conn = get_connection()
    cursor = conn.cursor()

    finished_at = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE scrape_runs
        SET finished_at = ?,
            status = ?,
            total_records = ?,
            error_message = ?
        WHERE id = ?
    """,
        (finished_at, status, total_records, error_message, run_id),
    )

    conn.commit()
    conn.close()


def insert_paper(arxiv_id, title, abstract, published_at, scraped_at, run_id):
    """
    Inserts a paper.
    Returns paper_id if inserted.
    Returns None if duplicate.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO papers (
                arxiv_id,
                title,
                abstract,
                published_at,
                scraped_at,
                run_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (arxiv_id, title, abstract, published_at, scraped_at, run_id),
        )

        conn.commit()
        paper_id = cursor.lastrowid
        conn.close()
        return paper_id

    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_or_create_author(name):
    """
    Returns author_id.
    Inserts author if not already present.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO authors (name)
            VALUES (?)
        """,
            (name,),
        )
        conn.commit()
        author_id = cursor.lastrowid
        conn.close()
        return author_id

    except sqlite3.IntegrityError:
        # Author already exists
        cursor.execute(
            """
            SELECT id FROM authors WHERE name = ?
        """,
            (name,),
        )
        author_id = cursor.fetchone()[0]
        conn.close()
        return author_id


def link_paper_author(paper_id, author_id):
    """
    Links a paper to an author.
    Duplicate links are safely ignored.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO paper_authors (paper_id, author_id)
            VALUES (?, ?)
        """,
            (paper_id, author_id),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Relationship already exists — ignore
        pass

    conn.close()
