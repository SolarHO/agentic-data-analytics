from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")


def check_key(file_name, columns):
    df = pd.read_csv(RAW_DIR / file_name)

    duplicated = df.duplicated(
        subset=columns,
        keep=False,
    )

    duplicate_count = duplicated.sum()

    print("=" * 70)
    print(f"FILE: {file_name}")
    print(f"KEY: {columns}")
    print(f"ROWS: {len(df):,}")
    print(f"DUPLICATED KEY ROWS: {duplicate_count:,}")

    if duplicate_count > 0:
        print("\n[DUPLICATE SAMPLE]")
        print(
            df.loc[duplicated, columns]
            .sort_values(columns)
            .head(10)
            .to_string(index=False)
        )

    print()


def main():
    tests = [
        (
            "olist_customers_dataset.csv",
            ["customer_id"],
        ),
        (
            "olist_orders_dataset.csv",
            ["order_id"],
        ),
        (
            "olist_products_dataset.csv",
            ["product_id"],
        ),
        (
            "olist_sellers_dataset.csv",
            ["seller_id"],
        ),
        (
            "olist_order_items_dataset.csv",
            ["order_id", "order_item_id"],
        ),
        (
            "olist_order_payments_dataset.csv",
            ["order_id", "payment_sequential"],
        ),
        (
            "olist_order_reviews_dataset.csv",
            ["review_id"],
        ),
        (
            "olist_order_reviews_dataset.csv",
            ["review_id", "order_id"],
        ),
        (
            "product_category_name_translation.csv",
            ["product_category_name"],
        ),
    ]

    for file_name, columns in tests:
        check_key(file_name, columns)


if __name__ == "__main__":
    main()
