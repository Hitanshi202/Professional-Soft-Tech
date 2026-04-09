from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict


class CSVProductError(ValueError):
    """Raised when the file format or row data is invalid."""


def _parse_price(raw: str, row_num: int) -> Decimal:
    s = raw.strip()
    if not s:
        raise CSVProductError(f"Row {row_num}: empty price")
    try:
        value = Decimal(s)
    except InvalidOperation as e:
        raise CSVProductError(f"Row {row_num}: invalid price {raw!r}") from e
    if value < 0:
        raise CSVProductError(f"Row {row_num}: negative price")
    return value


def stock_by_category(csv_path: str | Path) -> Dict[str, int]:
    """
    Read a CSV with columns: name, category, price, stock.

    Returns a dict mapping category -> sum of stock for that category.

    Raises:
        FileNotFoundError: If the path does not exist or is not a file.
        PermissionError: If the file cannot be read.
        CSVProductError: If headers are wrong or a row is invalid.
        OSError: Other OS-level read failures.
    """
    path = Path(csv_path)
    if path.is_dir():
        raise FileNotFoundError(f"Path is a directory, not a CSV file: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"CSV not found: {path}")

    required = {"name", "category", "price", "stock"}
    totals: Dict[str, int] = {}

    try:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise CSVProductError("CSV has no header row.")
            headers = {h.strip() for h in reader.fieldnames if h}
            if not required.issubset(headers):
                missing = required - headers
                raise CSVProductError(f"Missing required columns: {sorted(missing)}")

            for row_num, row in enumerate(reader, start=2):
                if row is None:
                    continue
                try:
                    name = (row.get("name") or "").strip()
                    if not name:
                        raise CSVProductError("empty product name")

                    category = (row.get("category") or "").strip()
                    if not category:
                        raise CSVProductError("empty category")

                    _parse_price(row.get("price") or "", row_num)

                    stock_raw = (row.get("stock") or "").strip()
                    stock = int(stock_raw)
                    if stock < 0:
                        raise CSVProductError("negative stock")
                except CSVProductError:
                    raise
                except (TypeError, ValueError) as e:
                    raise CSVProductError(
                        f"Row {row_num}: invalid stock — {e}"
                    ) from e

                totals[category] = totals.get(category, 0) + stock

    except FileNotFoundError:
        raise
    except PermissionError:
        raise
    except OSError as e:
        raise CSVProductError(f"Cannot read file: {e}") from e
    except UnicodeDecodeError as e:
        raise CSVProductError(f"File is not valid UTF-8: {e}") from e

    return totals


if __name__ == "__main__":
    import json

    sample = Path(__file__).resolve().parent / "data" / "sample_products.csv"
    print(json.dumps(stock_by_category(sample), indent=2))
