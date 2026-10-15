import json
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from app.db.postgres import engine


ROOT_DIR = Path(__file__).resolve().parents[1]

SQL_FILE = ROOT_DIR / "sql" / "gold_queries.sql"
OUTPUT_DIR = ROOT_DIR / "evaluation" / "gold_results"

TARGET_CASES = ["GQ03", "GQ04"]


def extract_gold_sql(content: str, case_id: str) -> str:
    pattern = rf"(?m)^-- {re.escape(case_id)}\b[^\n]*"

    match = re.search(pattern, content)

    if match is None:
        raise ValueError(f"Gold SQL not found: {case_id}")

    sql_start = content.find("SELECT", match.end())

    if sql_start == -1:
        raise ValueError(f"SELECT statement not found: {case_id}")

    sql_end = content.find(";", sql_start)

    if sql_end == -1:
        raise ValueError(f"SQL terminator not found: {case_id}")

    return content[sql_start:sql_end + 1]


def serialize_value(value):
    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return value


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sql_content = SQL_FILE.read_text(encoding="utf-8-sig")

    for case_id in TARGET_CASES:
        sql = extract_gold_sql(sql_content, case_id)

        with engine.connect() as connection:
            result = connection.execute(text(sql))

            rows = [
                {
                    key: serialize_value(value)
                    for key, value in row.items()
                }
                for row in result.mappings()
            ]

        output_path = OUTPUT_DIR / f"{case_id}.json"

        output_path.write_text(
            json.dumps(
                rows,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"{case_id}: {len(rows)} rows "
            f"saved to {output_path}"
        )


if __name__ == "__main__":
    main()