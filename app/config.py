from dotenv import load_dotenv
import os

load_dotenv()

MARKETAUX_API_TOKEN = os.getenv("MARKETAUX_API_TOKEN", "")
NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY", "")
QUERY_TERMS = [q.strip() for q in os.getenv("QUERY_TERMS", "Fed,earnings,CEO,merger").split(",") if q.strip()]
NEWSAPI_DOMAINS = os.getenv("NEWSAPI_DOMAINS", "")  # comma separated
USER_AGENT = "W&P-IBM-Hackathon-Ingestor/1.0 (contact: team@example.com)"
REQUEST_TIMEOUT = 20.0
