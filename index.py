import logging
import os

import openai

from settings import DB_PATH, EMBEDDING_MODEL, OPENAI_API_KEY, TABLE_NAME
from sqlite_helper import Index
from tools.semantic_search import semantic_search_tool

# Configure logging
logger = logging.getLogger(__name__)

_openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


def get_embedding(verses, model=EMBEDDING_MODEL):
    """Generates an embedding for the given text using the specified OpenAI model."""
    try:
        text = [verse.replace("\n", " ") for verse in verses]
        response = _openai_client.embeddings.create(input=text, model=model)
        return [i.embedding for i in response.data]
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


def read_file_content(filepath):
    """Reads the content of a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return None


def parse_file(content: str, filename: str) -> tuple[str, str, list[str]]:
    """Parses the content of a file and returns the url, poem_id, and verses."""
    lines = content.splitlines()

    url = ""
    poem_id = ""
    verses = []

    if not lines:
        logger.warning("Empty content provided to parse_file. Returning empty fields.")
        return url, poem_id, verses

    # 1. Extract URL from the first line
    url = lines[1].strip()

    # 2. Extract poem_id from URL
    # Assumes poem_id is like 'shX' or 'shXXX' and is a path component.
    # e.g., https://.../ghazal/sh1/ -> "sh1"
    if url:
        path_segments = [segment for segment in url.split("/") if segment]
        # Iterate backwards through path segments to find one starting with 'sh' followed by digits
        for i in range(len(path_segments) - 1, -1, -1):
            segment = path_segments[i]
            if segment.startswith("sh"):
                potential_num = segment[2:]  # Part after "sh"
                if potential_num.isdigit():
                    poem_id = segment
                    break  # Found the poem_id
        if not poem_id:
            raise ValueError(f"Could not extract poem_id of format 'sh<digits>' from URL: {url}")
    else:
        raise ValueError(f"URL is empty, cannot parse poem_id from it. {filename}")

    # 3. Extract Verses
    # Verses start from the 5th line (index 4)
    if len(lines) >= 5:
        # lines[4:] includes the 5th line till the end
        raw_verses = lines[4:]
        verses = [
            line.strip() for line in raw_verses if line.strip()
        ]  # Filter out any empty or whitespace-only lines

    return url, poem_id, verses


def index_directory(directory_path, index_instance: Index = None):
    """
    Walks a directory, embeds each file/chunk, and stores vectors in the given index instance.
    """
    if index_instance is None:
        idx = Index()
    else:
        idx = index_instance
    logger.info(f"Starting indexing for directory: {directory_path} into {idx.db_path}/{idx.table_name}")
    file_count = 0
    indexed_count = 0
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_count += 1
            # Skip common non-text or large binary files, and the index file itself
            if (
                file.startswith(".")
                or file == os.path.basename(idx.db_path)  # Skip the database file itself
                or file.endswith(
                    (
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".gif",
                        ".zip",
                        ".tar.gz",
                        ".exe",
                        ".dll",
                        ".so",
                        ".o",
                        ".pyc",
                        ".db-shm",
                        ".db-wal",
                    )
                )
            ):
                logger.debug(f"Skipping file: {file}")
                continue

            filepath = os.path.join(root, file)
            logger.debug(f"Processing file: {filepath}")

            content = read_file_content(filepath)
            if content:
                url, poem_id, verses = parse_file(content, file)
                embeddings = get_embedding(verses)  # Whole file embedding for simplicity
                if embeddings is not None:
                    idx.add_document(url, verses, embeddings)
                    indexed_count += 1
                else:
                    logger.warning(f"Could not generate embedding for {filepath}")
            else:
                logger.warning(f"Could not read content from {filepath}")

    logger.info(
        f"Finished indexing directory: {directory_path}. Processed {file_count} files, indexed {indexed_count} documents."
    )
    # No explicit save needed as add_document commits to SQLite.


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    logger.info("Running semantic search tool with sqlite-vec...")

    db_file = DB_PATH
    table = TABLE_NAME

    # Clean up old DB file for a fresh test run if it exists
    if os.path.exists(db_file):
        logger.info(f"Removing existing test database: {db_file}")
        os.remove(db_file)
    if os.path.exists(f"{db_file}-shm"):  # SQLite temporary files
        os.remove(f"{db_file}-shm")
    if os.path.exists(f"{db_file}-wal"):
        os.remove(f"{db_file}-wal")

    sample_docs_dir = "docs"
    if not os.path.exists(sample_docs_dir):
        raise FileNotFoundError(f"Directory {sample_docs_dir} not found")

    custom_index = Index()

    logger.info(f"Indexing '{sample_docs_dir}/' into {db_file}/{table}")
    index_directory(sample_docs_dir, index_instance=custom_index)

    # 7. Perform a search
    search_query = "شمع"
    logger.info(f"Performing search: '{search_query}'")
    search_results = semantic_search_tool(query=search_query, top_k=2, index_instance=custom_index)

    if search_results:
        logger.info("Search results:")
        for result in search_results:
            # Ensure score is float for formatting. It should be.
            score = float(result.get("score", 0.0))
            logger.info(f"  File: {result['url']}")
            logger.info(f"  Score: {score:.4f} (higher is better, 1-distance)")
            logger.info(f"  Chunk: '{result['verse']}'")
            logger.info("-" * 20)
    else:
        logger.info("No results found.")

    del custom_index

    logger.info("index job finished")
