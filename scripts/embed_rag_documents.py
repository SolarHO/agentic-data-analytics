
import os

from dotenv import load_dotenv
from pgvector.psycopg import register_vector
from psycopg import connect
from psycopg.rows import dict_row
from sentence_transformers import SentenceTransformer

from app.rag.document_builder import build_rag_documents


MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

EMBEDDING_DIMENSIONS = 384


def main():
    load_dotenv()

    documents = build_rag_documents()

    print(f"Documents: {len(documents)}")
    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(
        MODEL_NAME,
        device="cpu",
    )

    contents = [
        document["content"]
        for document in documents
    ]

    print("Generating embeddings...")

    embeddings = model.encode(
        contents,
        batch_size=16,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    assert embeddings.shape == (
        len(documents),
        EMBEDDING_DIMENSIONS,
    )

    connection_info = {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ["DB_PORT"]),
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
    }

    with connect(**connection_info, row_factory=dict_row) as conn:
        register_vector(conn)

        with conn.cursor() as cursor:
            for document, embedding in zip(
                documents,
                embeddings,
            ):
                cursor.execute(
                    """
                    INSERT INTO rag_documents (
                        document_id,
                        doc_type,
                        name,
                        content,
                        embedding,
                        embedding_model
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (document_id)
                    DO UPDATE SET
                        doc_type = EXCLUDED.doc_type,
                        name = EXCLUDED.name,
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        embedding_model = EXCLUDED.embedding_model,
                        updated_at = NOW()
                    """,
                    (
                        document["id"],
                        document["doc_type"],
                        document["name"],
                        document["content"],
                        embedding,
                        MODEL_NAME,
                    ),
                )

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS document_count,
                    COUNT(DISTINCT doc_type) AS type_count
                FROM rag_documents
                """
            )

            result = cursor.fetchone()

    print("Embedding ingestion complete.")
    print(f"Stored documents: {result['document_count']}")
    print(f"Document types: {result['type_count']}")


if __name__ == "__main__":
    main()
