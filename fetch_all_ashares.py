import os
import argparse
import akshare as ak


def main():
    parser = argparse.ArgumentParser(
        description="Export all A-share stock codes and names using akshare."
    )

    parser.add_argument(
        "--out",
        type=str,
        default="./all_stocks.csv",
        help="Output CSV file path (default: ./all_stocks.csv)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    output_path = args.out

    # Ensure directory exists
    dir_name = os.path.dirname(output_path)
    if dir_name and not os.path.exists(dir_name):
        if args.verbose:
            print(f"[INFO] Creating directory: {dir_name}")
        os.makedirs(dir_name)

    if args.verbose:
        print("[INFO] Fetching A-share stock list from akshare...")

    # Fetch data
    all_stocks_akshare = ak.stock_info_a_code_name()

    if args.verbose:
        print(f"[INFO] Retrieved {len(all_stocks_akshare)} records.")
        print(f"[INFO] Saving to: {output_path}")

    # Save CSV
    all_stocks_akshare.to_csv(output_path, index=False, encoding="utf-8-sig")

    if args.verbose:
        print("[INFO] File saved successfully.")
        print("[INFO] Preview (first 5 rows):")
        print(all_stocks_akshare.head())


if __name__ == "__main__":
    main()