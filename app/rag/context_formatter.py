
from collections.abc import Sequence
from typing import Any


def format_retrieved_context(
    documents: Sequence[dict[str, Any]],
) -> str:
    """
    Format retrieved documents into SQL generation context.
    """

    if not documents:
        raise ValueError("No context documents provided.")

    sections = []
    seen = set()

    for doc in documents:
        document_id = doc["document_id"]

        if document_id in seen:
            continue

        content = doc["content"].strip()

        if not content:
            raise ValueError(
                f"Empty document content: {document_id}"
            )

        sections.append(
            f"[{document_id}]\n{content}"
        )

        seen.add(document_id)

    return "\n\n".join(sections)
