from __future__ import annotations

import os
from contextlib import contextmanager
from decimal import Decimal
from typing import Any, Dict, Generator, List
from urllib.parse import urlparse

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:  # optional dependency; install with: pip install psycopg2-binary
    psycopg2 = None  # type: ignore[assignment]
    RealDictCursor = None  # type: ignore[assignment]


def _require_driver() -> None:
    if psycopg2 is None:
        raise ImportError(
            "Section 3 needs psycopg2. Install with: pip install psycopg2-binary "
            "(use a venv if your system blocks pip install)."
        ) from None


def _connect():
    _require_driver()
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        parsed = urlparse(url)
        if parsed.scheme not in ("postgresql", "postgres"):
            raise ValueError(
                "DATABASE_URL must start with postgresql:// or postgres://"
            )
        dbname = (parsed.path or "/").lstrip("/") or "postgres"
        return psycopg2.connect(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            dbname=dbname,
            user=parsed.username or os.environ.get("PGUSER", "postgres"),
            password=parsed.password or "",
        )
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ.get("PGDATABASE", "erp_test"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", ""),
    )


@contextmanager
def get_connection() -> Generator[Any, None, None]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        category VARCHAR(128) NOT NULL,
        price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
        stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS customers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER NOT NULL REFERENCES customers (id) ON DELETE RESTRICT,
        product_id INTEGER NOT NULL REFERENCES products (id) ON DELETE RESTRICT,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        unit_price NUMERIC(12, 2) NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    );
    """,
]


def create_tables(conn) -> None:
    with conn.cursor() as cur:
        for stmt in DDL_STATEMENTS:
            cur.execute(stmt)


def insert_product(
    conn,
    name: str,
    category: str,
    price: Decimal | float | str,
    stock: int,
) -> int:
    p = price if isinstance(price, Decimal) else Decimal(str(price))
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO products (name, category, price, stock)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (name, category, p, stock),
        )
        row = cur.fetchone()
        return int(row[0])


def insert_customer(conn, name: str, email: str | None = None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO customers (name, email)
            VALUES (%s, %s)
            RETURNING id;
            """,
            (name, email),
        )
        return int(cur.fetchone()[0])


def fetch_orders_for_customer(conn, customer_id: int) -> List[Dict[str, Any]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT o.id, o.quantity, o.unit_price, o.created_at,
                   p.name AS product_name, c.name AS customer_name
            FROM orders o
            JOIN products p ON p.id = o.product_id
            JOIN customers c ON c.id = o.customer_id
            WHERE o.customer_id = %s
            ORDER BY o.created_at DESC;
            """,
            (customer_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def place_order_update_stock(
    conn,
    customer_id: int,
    product_id: int,
    quantity: int,
) -> int:
    """
    Insert an order row and decrement product stock in one transaction.
    Uses row-level lock on the product row for safe concurrent updates.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, price, stock FROM products WHERE id = %s FOR UPDATE;",
            (product_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("product not found")
        _, unit_price, stock = row
        if stock < quantity:
            raise ValueError("insufficient stock")

        cur.execute(
            """
            UPDATE products SET stock = stock - %s WHERE id = %s;
            """,
            (quantity, product_id),
        )
        cur.execute(
            """
            INSERT INTO orders (customer_id, product_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (customer_id, product_id, quantity, unit_price),
        )
        oid = cur.fetchone()[0]
        return int(oid)


def seed_demo_customer(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO customers (name, email)
            VALUES ('Demo User', 'demo@example.com')
            ON CONFLICT (email) DO NOTHING
            RETURNING id;
            """
        )
        r = cur.fetchone()
        if r:
            return int(r[0])
        cur.execute("SELECT id FROM customers WHERE email = %s;", ("demo@example.com",))
        row = cur.fetchone()
        if not row:
            raise RuntimeError("failed to seed demo customer")
        return int(row[0])


if __name__ == "__main__":
    try:
        with get_connection() as c:
            create_tables(c)
            pid = insert_product(c, "Demo SKU", "Misc", "9.99", 100)
            cid = seed_demo_customer(c)
            oid = place_order_update_stock(c, cid, pid, 2)
            orders = fetch_orders_for_customer(c, cid)
            print("order id:", oid, "orders:", orders)
    except Exception as e:
        print("DB example skipped (set PG* or DATABASE_URL when a server is available):", e)
