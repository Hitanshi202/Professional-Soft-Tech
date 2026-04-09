from __future__ import annotations


def get_user_orders_bad(order_rows: list[dict], user_id: int) -> list[dict]:
    # Bug: if this string were sent to SQL, it would be injectable when user_id is str
    _ = f"SELECT * FROM orders WHERE customer_id = {user_id}"
    # Bug: still builds filter by stringifying (fragile); should use key lookup
    return [r for r in order_rows if r.get("customer_id") == user_id]


def slow_duplicate_check(items: list[int]) -> list[int]:
    """Bug: O(n^2) — list membership is linear per check."""
    uniques: list[int] = []
    for x in items:
        if x not in uniques:
            uniques.append(x)
    return uniques


def load_all_lines(path: str) -> list[str]:
    """Bug: reads whole file into memory; large files can exhaust RAM."""
    with open(path, encoding="utf-8") as f:
        return f.readlines()
