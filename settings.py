import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

# text-embedding-3-small
# text-embedding-3-large
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# other possible o4-mini
CHAT_MODEL = "gpt-4.1-mini"

DB_PATH = "semantic_index.db"
TABLE_NAME = "embeddings_vec"

LOGFIRE_API_KEY = os.environ.get("LOGFIRE_API_KEY")
if LOGFIRE_API_KEY:
    import logfire

    logfire.configure(token=LOGFIRE_API_KEY, console=False)
    logfire.instrument_openai()
