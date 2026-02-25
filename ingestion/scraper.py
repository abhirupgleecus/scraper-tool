import requests
from bs4 import BeautifulSoup
from config import ARXIV_BASE_URL, ARXIV_LIST_PATH
import time


from persistence.repository import (
    create_scrape_run,
    update_scrape_run,
    insert_paper,
    get_or_create_author,
    link_paper_author,
)
from datetime import datetime
from config import ARXIV_RESULTS_PER_PAGE

def fetch_arxiv_page(skip=0, show=25):
    """
    Fetch paginated arXiv listing page.
    """
    url = f"{ARXIV_BASE_URL}{ARXIV_LIST_PATH}?skip={skip}&show={show}"
    print(f"Fetching URL: {url}")

    response = requests.get(url, timeout=10)
    print("Status Code:", response.status_code)
    response.raise_for_status()

    return response.text


def fetch_abstract_data(url):
    """
    Fetch abstract page and extract abstract text + published date.
    """
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract abstract text
    abstract_block = soup.find("blockquote", class_="abstract")
    abstract_text = (
        abstract_block.text.replace("Abstract:", "").strip() if abstract_block else None
    )

    # Extract submission date safely
    submission_div = soup.find("div", class_="submission-history")

    published_at = None
    if submission_div:
        text = submission_div.get_text(strip=True)
        # Example format:
        # "Submission history[v1] Tue, 20 Feb 2026 14:32:10 UTC (1234 KB)"
        import re

        match = re.search(r"\d{1,2}\s\w+\s\d{4}", text)
        if match:
            from datetime import datetime

            raw_date = match.group(0)  # e.g., "23 Feb 2026"
            parsed_date = datetime.strptime(raw_date, "%d %b %Y")
            published_at = parsed_date.strftime("%Y-%m-%d")

    return abstract_text, published_at


def parse_papers(html):
    """
    Parses recent papers from arXiv page.
    Returns a list of structured paper dictionaries.
    """
    soup = BeautifulSoup(html, "html.parser")
    dl = soup.find("dl")

    if not dl:
        print("No paper list found.")
        return []

    papers = []
    dts = dl.find_all("dt")
    dds = dl.find_all("dd")

    for dt, dd in zip(dts, dds):

        # Abstract URL
        id_link = dt.find("a", title="Abstract")
        relative_link = id_link["href"]  # e.g., /abs/2602.18291
        abstract_url = ARXIV_BASE_URL + relative_link

        # Clean arXiv ID
        arxiv_id = id_link.text.replace("arXiv:", "").strip()

        # Title
        title_div = dd.find("div", class_="list-title")
        title = title_div.text.replace("Title:", "").strip()

        # Authors
        authors_div = dd.find("div", class_="list-authors")
        authors = [a.text.strip() for a in authors_div.find_all("a")]

        paper = {
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "abstract_url": abstract_url,
        }

        papers.append(paper)

    return papers



def run_scraper():
    """
    Full ingestion pipeline execution.
    """
    run_id = create_scrape_run()
    total_inserted = 0

    try:
        skip = 0
        show = ARXIV_RESULTS_PER_PAGE

        # page limit: to prevent infinite loop during development, can be removed later
        max_pages = 50
        page_count = 0

        while True:

            if page_count >= max_pages:
                print("Reached max page limit. Stopping pagination.")
                break

            html = fetch_arxiv_page(skip=skip, show=show)
            papers = parse_papers(html)

            if not papers:
                break

            for paper in papers:
                # Fetch abstract and published date
                abstract, published_at = fetch_abstract_data(paper["abstract_url"])
                # Insert paper and get paper_id
                paper_id = insert_paper(
                    arxiv_id=paper["arxiv_id"],
                    title=paper["title"],
                    abstract=abstract,
                    published_at=published_at,
                    scraped_at=datetime.utcnow().isoformat(),
                    run_id=run_id,
                )

                if paper_id:
                    total_inserted += 1

                    for author_name in paper["authors"]:
                        author_id = get_or_create_author(author_name)
                        link_paper_author(paper_id, author_id)
            skip += show
            page_count += 1
            print(f"Page {page_count}: Parsed {len(papers)} papers")

            time.sleep(2)
        update_scrape_run(
            run_id=run_id,
            status="success",
            total_records=total_inserted,
        )

        print(f"\nScrape completed. Inserted {total_inserted} new papers.")

    except Exception as e:
        update_scrape_run(
            run_id=run_id,
            status="failed",
            total_records=total_inserted,
            error_message=str(e),
        )
        print("Scrape failed:", e)
        raise

    except KeyboardInterrupt:
        update_scrape_run(
            run_id=run_id,
            status="failed",
            total_records=total_inserted,
            error_message="Interrupted by user",
        )
        print("Scrape interrupted by user.")
        raise


if __name__ == "__main__":
    run_scraper()
