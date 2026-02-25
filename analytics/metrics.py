from persistence.repository import get_connection


def get_daily_counts():
    """
    Returns list of (published_at, count)
    sorted by date ascending.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT published_at, COUNT(*)
        FROM papers
        GROUP BY published_at
        ORDER BY published_at ASC;
    """)

    results = cursor.fetchall()
    conn.close()
    return results


def get_growth_vs_yesterday():
    """
    Calculates % change between latest day
    and previous day.
    """
    data = get_daily_counts()

    if len(data) < 2:
        return None

    latest_date, latest_count = data[-1]
    prev_date, prev_count = data[-2]

    if prev_count == 0:
        return None

    pct_change = ((latest_count - prev_count) / prev_count) * 100

    return {
        "latest_date": latest_date,
        "latest_count": latest_count,
        "previous_date": prev_date,
        "previous_count": prev_count,
        "percentage_change": round(pct_change, 2),
    }


def get_top_authors(limit=10):
    """
    Returns top authors by paper count.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.name, COUNT(*) as paper_count
        FROM authors a
        JOIN paper_authors pa ON a.id = pa.author_id
        GROUP BY a.id
        ORDER BY paper_count DESC
        LIMIT ?;
    """, (limit,))

    results = cursor.fetchall()
    conn.close()
    return results


def get_run_metrics():
    """
    Returns:
    - count of runs by status
    - average papers per successful run
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status, COUNT(*)
        FROM scrape_runs
        GROUP BY status;
    """)
    status_counts = cursor.fetchall()

    cursor.execute("""
        SELECT AVG(total_records)
        FROM scrape_runs
        WHERE status = 'success';
    """)
    avg_per_run = cursor.fetchone()[0]

    conn.close()

    return {
        "status_counts": status_counts,
        "avg_per_run": round(avg_per_run or 0, 2)
    }


def get_peak_day():
    """
    Returns day with highest submission count.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT published_at, COUNT(*) as cnt
        FROM papers
        GROUP BY published_at
        ORDER BY cnt DESC
        LIMIT 1;
    """)

    result = cursor.fetchone()
    conn.close()
    return result

def get_all_runs():
    """
    Returns full scrape run history ordered by most recent first.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, started_at, status, total_records, error_message
        FROM scrape_runs
        ORDER BY id DESC;
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows