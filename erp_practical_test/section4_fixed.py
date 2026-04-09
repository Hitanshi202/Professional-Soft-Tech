from __future__ import annotations

from typing import Any, Dict, Generator, Iterable, List


def get_user_orders(order_rows: Iterable[Dict[str, Any]], user_id: int) -> List[Dict[str, Any]]:
    # Safe pattern: compare in Python with typed id, or parameterized SQL in real DB code
    return [r for r in order_rows if r.get("customer_id") == user_id]


def unique_preserve_order(items: list[int]) -> list[int]:
    return list(dict.fromkeys(items))


def iter_lines(path: str) -> Generator[str, None, None]:
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n")
