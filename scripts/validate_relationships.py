from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")


def load(name, columns):
    return pd.read_csv(
        RAW_DIR / name,
        usecols=columns,
    )


def check_fk(
    child_name,
    child_column,
    parent_name,
    parent_column,
):
    child = load(child_name, [child_column])
    parent = load(parent_name, [parent_column])

    child_values = set(
        child[child_column].dropna().unique()
    )

    parent_values = set(
        parent[parent_column].dropna().unique()
    )

    missing = child_values - parent_values

    print("=" * 70)
    print(
        f"{child_name}.{child_column}"
        f" -> "
        f"{parent_name}.{parent_column}"
    )

    print(f"CHILD UNIQUE: {len(child_values):,}")
    print(f"PARENT UNIQUE: {len(parent_values):,}")
    print(f"MISSING FK VALUES: {len(missing):,}")

    if missing:
        print("SAMPLE:")
        print(list(missing)[:10])

    print()


def main():

    checks = [
        (
            "olist_orders_dataset.csv",
            "customer_id",
            "olist_customers_dataset.csv",
            "customer_id",
        ),

        (
            "olist_order_items_dataset.csv",
            "order_id",
            "olist_orders_dataset.csv",
            "order_id",
        ),

        (
            "olist_order_items_dataset.csv",
            "product_id",
            "olist_products_dataset.csv",
            "product_id",
        ),

        (
            "olist_order_items_dataset.csv",
            "seller_id",
            "olist_sellers_dataset.csv",
            "seller_id",
        ),

        (
            "olist_order_payments_dataset.csv",
            "order_id",
            "olist_orders_dataset.csv",
            "order_id",
        ),

        (
            "olist_order_reviews_dataset.csv",
            "order_id",
            "olist_orders_dataset.csv",
            "order_id",
        ),

        (
            "olist_products_dataset.csv",
            "product_category_name",
            "product_category_name_translation.csv",
            "product_category_name",
        ),
    ]

    for check in checks:
        check_fk(*check)


if __name__ == "__main__":
    main()
