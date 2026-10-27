
import os
from functools import lru_cache

from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from psycopg import connect
from psycopg.rows import dict_row
from sentence_transformers import SentenceTransformer


MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer(
        MODEL_NAME,
        device="cpu",
    )


def get_read_connection_info():
    load_dotenv()

    return {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ["DB_PORT"]),
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_READ_USER"],
        "password": os.environ["DB_READ_PASSWORD"],
    }


def search_context(
    question: str,
    top_k: int = 5,
) -> list[dict]:
    question = question.strip()

    if not question:
        raise ValueError("Question must not be empty.")

    if not 1 <= top_k <= 33:
        raise ValueError("top_k must be between 1 and 33.")

    model = get_embedding_model()

    query_embedding = model.encode(
        question,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    with connect(
        **get_read_connection_info(),
        row_factory=dict_row,
    ) as conn:
        register_vector(conn)

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    document_id,
                    doc_type,
                    name,
                    content,
                    embedding_model,
                    1 - (embedding <=> %s) AS similarity
                FROM public.rag_documents
                WHERE embedding_model = %s
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (
                    query_embedding,
                    MODEL_NAME,
                    query_embedding,
                    top_k,
                ),
            )

            results = cursor.fetchall()

    return results
