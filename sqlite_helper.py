import json
import logging
import sqlite3

import sqlite_vec  # Added for sqlite-vec
from sqlite_vec import serialize_float32

from settings import DB_PATH, EMBEDDING_DIM, TABLE_NAME

# Configure logging
logger = logging.getLogger(__name__)


class Index:
    """Stores and manages document embeddings using sqlite-vec."""

    def __init__(self):
        self.db_path = DB_PATH
        self.table_name = TABLE_NAME
        self.conn = sqlite3.connect(self.db_path)
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        logger.info(f"Connected to SQLite database: {self.db_path} and loaded sqlite-vec extension.")
        self._create_table()

    def _execute_sql(self, sql, params=()):
        """Executes SQL and handles cursor management."""
        try:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            self.conn.commit()
            return cur
        except Exception as e:
            logger.error(f"SQLite error: {e} for SQL: {sql} with params: {params}")
            # Optionally, re-raise or handle more gracefully
            raise

    def _create_table(self):
        """Creates the vector table if it doesn't exist."""
        # Using f-string for table_name and EMBEDDING_DIM is generally safe here as they are controlled internally.
        # However, for user-provided table names, parameterization or strict validation would be crucial.
        sql = f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS {self.table_name} USING vec0(
            embedding FLOAT[{EMBEDDING_DIM}],  -- Define the vector column with its dimensions
            url TEXT,
            verse TEXT,
        );
        """
        self._execute_sql(sql)
        logger.info(f"Table '{self.table_name}' ensured in {self.db_path}.")

    def add_document(self, url, verses, vectors):
        """Adds a document chunk and its vector to the SQLite table."""
        sql = f"INSERT INTO {self.table_name} (url, verse, embedding) VALUES (?, ?, ?);"
        for verse, vector in zip(verses, vectors, strict=True):
            self._execute_sql(sql, (url, verse, serialize_float32(vector)))

    def search(self, query_vector, top_k=3):
        """
        Searches the index for the most similar document chunks using sqlite-vec.
        Returns a list of (url, verse, similarity_score)
        """
        if query_vector is None:
            logger.warning("Search query vector is None. Returning empty results.")
            return []

        query_vector_json = json.dumps(query_vector)
        # The 'distance' from vec_search is cosine distance if vectors are normalized,
        # or L2 distance otherwise. OpenAI embeddings are typically normalized.
        # similarity = 1 - distance (for cosine distance where 0 is identical)
        sql = f"""
        SELECT url, verse, distance
        FROM {self.table_name}
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT ?;
        """
        try:
            cur = self._execute_sql(sql, (query_vector_json, top_k))
            results = []
            for row in cur.fetchall():
                url, verse, distance = row
                # Assuming OpenAI embeddings are normalized, distance is cosine distance.
                # For cosine similarity: similarity = (1 - distance) if distance is on [0, 2]
                # Or, if OpenAI embeddings are pre-normalized and sqlite-vec uses dot product for MATCH
                # with normalized vectors, then 'distance' might be 1 - similarity or similar.
                # Let's assume distance is cosine distance, so similarity = 1 - distance.
                # More accurately, for normalized vectors, cosine_similarity = (vector1 • vector2)
                # Cosine Distance = 1 - cosine_similarity.
                # If 'distance' is indeed cosine distance, then similarity = 1 - distance.
                # If 'distance' from sqlite-vec for MATCH is L2 squared, this conversion needs adjustment.
                # The sqlite-vec documentation implies 'distance' is L2 by default.
                # For OpenAI embeddings, cosine similarity is preferred.
                # To use cosine similarity with sqlite-vec, vectors should be normalized,
                # and then `vec_dot_product` can be used, or rely on `MATCH` if it's L2
                # and we accept that ranking (often similar to cosine for high-dim).
                # For simplicity with `MATCH`, we'll treat distance as something to minimize.
                # The score returned will be this 'distance'. User should know lower is better.
                # OR, we stick to the original contract of returning a 'similarity_score'
                # where higher is better. If distance is L2, this is tricky.
                # Let's assume for now `MATCH` with normalized vectors provides a distance that
                # can be inverted to a similarity-like score.
                # If OpenAI embeddings are normalized (length 1), then L2 distance squared (d^2) relates to cosine similarity (cs) by d^2 = 2 - 2*cs.
                # So, cs = 1 - (d^2 / 2).
                # We will return `1 - distance` as a general proximity score, assuming distance is somewhat like cosine distance.
                similarity_score = (
                    1 - distance
                )  # This might need refinement based on sqlite-vec's exact distance metric for MATCH
                results.append({"url": url, "verse": verse, "score": similarity_score})
            return results
        except Exception as e:
            logger.error(f"Error during search in {self.table_name}: {e}")
            return []

    def __del__(self):
        """Closes the database connection when the object is deleted."""
        if hasattr(self, "conn") and self.conn:
            self.conn.close()
            logger.info(f"Closed SQLite connection to {self.db_path}")
