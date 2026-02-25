import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database
DB_PATH = os.path.join(BASE_DIR, "db", "arxiv_monitor.db")

# arXiv
ARXIV_BASE_URL = "https://arxiv.org"
ARXIV_CATEGORY = "cs.AI"
ARXIV_LIST_PATH = f"/list/{ARXIV_CATEGORY}/recent"
ARXIV_RESULTS_PER_PAGE = 25