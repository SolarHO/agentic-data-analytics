from pathlib import Path

import pandas as pd
from sqlalchemy import text

from app.db.postgres import engine


RAW_DIR = Path("data/raw")


TABLE_CONFIG = [
    ("customers", "olist_customers_dataset.csv"),
    ("category_translation", "product_category_name_translation.csv"),
    ("products", "olist_products_dataset.csv"),
    ("sellers", "olist_sellers_dataset.csv"),
    ("orders", "olist_orders_dataset.csv"),
    ("order_items", "olist_order_items_dataset.csv"),
    ("order_payments", "olist_order_payments_dataset.csv"),
    ("order_reviews", "olist_order_reviews_dataset.csv"),
    ("geolocation", "olist_geolocation_dataset.csv"),
]


DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": [
        "shipping_limit_date",
    ],
    "order_reviews": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
}


def prepare_dataframe(table_name: str, file_name: str) -> pd.DataFrame:
    file_path = RAW_DIR / file_name

    print(f"\nReading {file_name}...")

    df = pd.read_csv(file_path)

    # Olist 원본 컬럼명의 오타를 DB 컬럼명에 맞게 수정
    if table_name == "products":
        df = df.rename(
            columns={
                "product_name_lenght": "product_name_length",
                "product_description_lenght": "product_description_length",
            }
        )

    # 문자열로 읽힌 날짜를 실제 datetime으로 변환
    for column in DATE_COLUMNS.get(table_name, []):
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
        )

    # products의 nullable 정수성 컬럼 정리
    if table_name == "products":
        integer_columns = [
            "product_name_length",
            "product_description_length",
            "product_photos_qty",
        ]

        for column in integer_columns:
            df[column] = df[column].astype("Int64")

    return df


def clear_tables() -> None:
    print("\nClearing existing data...")

    sql = text(
        """
        TRUNCATE TABLE
            geolocation,
            order_reviews,
            order_payments,
            order_items,
            orders,
            sellers,
            products,
            category_translation,
            customers
        RESTART IDENTITY CASCADE;
        """
    )

    with engine.begin() as connection:
        connection.execute(sql)

    print("Existing data cleared.")


def load_table(table_name: str, file_name: str) -> int:
    df = prepare_dataframe(table_name, file_name)

    csv_count = len(df)

    print(
        f"Loading {table_name}: "
        f"{csv_count:,} rows..."
    )

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )

    with engine.connect() as connection:
        db_count = connection.execute(
            text(f'SELECT COUNT(*) FROM "{table_name}"')
        ).scalar_one()

    if csv_count != db_count:
        raise RuntimeError(
            f"Row count mismatch for {table_name}: "
            f"CSV={csv_count:,}, DB={db_count:,}"
        )

    print(
        f"OK: {table_name} "
        f"(CSV={csv_count:,}, DB={db_count:,})"
    )

    return db_count


def main() -> None:
    print("=" * 70)
    print("Olist PostgreSQL Ingestion")
    print("=" * 70)

    clear_tables()

    total_rows = 0

    for table_name, file_name in TABLE_CONFIG:
        count = load_table(
            table_name,
            file_name,
        )
        total_rows += count

    print("\n" + "=" * 70)
    print("INGESTION COMPLETED")
    print(f"TOTAL ROWS: {total_rows:,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
