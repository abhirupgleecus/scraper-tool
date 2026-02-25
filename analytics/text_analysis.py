import re
from collections import Counter
from persistence.repository import get_connection


STOPWORDS = {
    
    "the", "and", "of", "in", "to", "a", "for", "with", "on",
    "is", "we", "that", "this", "by", "an", "are", "as", "be",
    "our", "from", "at", "or", "can", "their", "these", "which",
    "models", "across", "while", "training", "framework", "using",
    "use", "used", "also", "have", "has", "but", "not", "they",
    "it", "its", "than", "may", "more", "other", "such", "all",
    "method", "methods", "results", "model", "data", "approach",
    "problem", "based", "learning", "network", "networks",
    "performance", "analysis", "paper", "propose", "proposed",
    "system", "systems", "task", "tasks", "dataset", "datasets",
    "experiment", "experiments", "show", "shown", "showed",
    "showing", "result", "demonstrate", "demonstrated",
    "demonstrating","public","object","objects","real","world","real-world",
    "still","many","much","different","new","novel","significant","significantly",
    ""

}


def get_all_abstracts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT abstract
        FROM papers
        WHERE abstract IS NOT NULL;
    """)

    abstracts = [row[0] for row in cursor.fetchall()]
    conn.close()

    return abstracts


def get_top_keywords(limit=10):
    abstracts = get_all_abstracts()

    words = []

    for abstract in abstracts:
        cleaned = re.sub(r"[^a-zA-Z\s]", "", abstract.lower())
        tokens = cleaned.split()

        filtered = [w for w in tokens if w not in STOPWORDS and len(w) > 3]
        words.extend(filtered)

    counter = Counter(words)
    return counter.most_common(limit)


def get_daily_keyword_counts():
    """
    Returns:
    {
        '2026-02-22': Counter({...}),
        '2026-02-23': Counter({...}),
    }
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT published_at, abstract
        FROM papers
        WHERE abstract IS NOT NULL
        ORDER BY published_at;
    """)

    rows = cursor.fetchall()
    conn.close()

    from collections import defaultdict

    daily_counts = defaultdict(Counter)

    for date, abstract in rows:
        if not date:
            continue

        cleaned = re.sub(r"[^a-zA-Z\s]", "", abstract.lower())
        tokens = cleaned.split()
        filtered = [w for w in tokens if w not in STOPWORDS and len(w) > 3]

        daily_counts[date].update(filtered)

    return dict(daily_counts)


def get_trending_topics(limit=10):
    daily = get_daily_keyword_counts()

    if len(daily) < 2:
        return []

    sorted_dates = sorted(daily.keys())
    latest = sorted_dates[-1]
    previous = sorted_dates[-2]

    latest_counter = daily[latest]
    previous_counter = daily[previous]

    momentum = []

    for word, latest_count in latest_counter.items():
        prev_count = previous_counter.get(word, 0)

        if prev_count == 0 and latest_count > 2:
            growth = 100.0
        elif prev_count > 0:
            growth = ((latest_count - prev_count) / prev_count) * 100
        else:
            continue

        momentum.append((word, latest_count, prev_count, round(growth, 2)))

    momentum.sort(key=lambda x: x[3], reverse=True)

    return {
        "latest_date": latest,
        "previous_date": previous,
        "top_trending": momentum[:limit],
    }