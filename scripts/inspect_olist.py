from pathlib import Path

import pandas as pd


RAW_DIR = Path("data/raw")


def inspect_csv(file_path: Path) -> None:
    df = pd.read_csv(file_path)

    print("=" * 80)
    print(f"FILE: {file_path.name}")
    print(f"ROWS: {len(df):,}")
    print(f"COLUMNS: {len(df.columns)}")
    print(f"DUPLICATE ROWS: {df.duplicated().sum():,}")

    print("\n[COLUMNS / DTYPES / NULLS]")

    for column in df.columns:
        print(
            f"{column:<40} "
            f"type={str(df[column].dtype):<10} "
            f"null={df[column].isna().sum():>7,} "
            f"unique={df[column].nunique(dropna=True):>7,}"
        )

    print("\n[SAMPLE]")
    print(df.head(3).to_string(index=False))
    print()


def main() -> None:
    csv_files = sorted(RAW_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {RAW_DIR.resolve()}"
        )

    print(f"Found {len(csv_files)} CSV files.\n")

    for file_path in csv_files:
        inspect_csv(file_path)


if __name__ == "__main__":
    main()
