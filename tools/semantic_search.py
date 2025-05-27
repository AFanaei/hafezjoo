import logging

import openai

from settings import EMBEDDING_MODEL, OPENAI_API_KEY
from sqlite_helper import Index

# Configure logging
logger = logging.getLogger(__name__)


_openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


def get_embedding(text, model=EMBEDDING_MODEL):
    """Generates an embedding for the given text using the specified OpenAI model."""
    try:
        text = text.replace("\n", " ")
        response = _openai_client.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


def semantic_search_tool(query: str, top_k: int = 3, index_instance: Index = None) -> list[dict]:
    """
    find most top_k similar verses from hafez to the query

    Args:
        query: The search query string.
        top_k: The number of top verses

    Returns:
        A list of dictionaries, where each dictionary contains:
        - 'url': url to the matched poem.
        - 'verse': The matched verse.
        - 'score': The similarity score (higher is better, derived from distance).
    """
    if index_instance is None:
        index = Index()
    else:
        index = index_instance

    logger.info(f"Executing semantic search for query: '{query}' with top_k={top_k}")
    if not query:
        logger.warning("Semantic search query is empty.")
        return []

    query_embedding = get_embedding(query)
    if query_embedding is None:
        logger.error("Failed to generate embedding for the query.")
        return []

    results = index.search(query_embedding, top_k=top_k)
    logger.info(f"Found {len(results)} results for query '{query}'.")
    return results
