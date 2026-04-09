# ERP Practical Test (Python)

Small, self-contained exercises for core Python, an in-memory ERP-style module, optional PostgreSQL integration, and a debugging exercise. **No Docker or local database is required** to use Sections 1, 2, and 4.

## Requirements

- **Python 3.10+** (uses modern type hints)
- **Dependencies**: Sections 1, 2, and 4 use only the standard library. Section 3 optionally uses `psycopg2-binary` when you connect to PostgreSQL.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

On systems where the OS manages Python (PEP 668), use a virtual environment as above instead of installing packages globally.

## Project layout

| File | Description |
|------|-------------|
| `section1_core_csv.py` | Read a product CSV; return total **stock per category** with validation and error handling |
| `section2_erp_module.py` | In-memory **ERPInventory**: add products, record sales, summary report |
| `section3_database.py` | **PostgreSQL**: create tables, insert products, fetch orders, place orders and update stock |
| `section4_buggy.py` | Intentional bugs (candidate exercise) |
| `section4_fixed.py` | Reference fixes and patterns |
| `data/sample_products.csv` | Sample input for Section 1 |

## Running

**Section 1 — CSV**

```bash
python section1_core_csv.py
```

Uses `data/sample_products.csv` relative to the script. Pass another path to `stock_by_category()` from code or a small wrapper.

**Section 2 — ERP module**

```bash
python section2_erp_module.py
```

**Section 3 — Database (optional)**

1. Have a **PostgreSQL** instance available (cloud, shared dev server, etc.).
2. Install dependencies: `pip install -r requirements.txt`
3. Set connection environment variables, for example:

```bash
export PGHOST=your.host PGPORT=5432 PGDATABASE=erp_test PGUSER=your_user PGPASSWORD=your_secret
```

Or a single URL:

```bash
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

Then:

```bash
python section3_database.py
```

If `psycopg2` is not installed or the server is unreachable, the script prints a short message and exits without crashing.

**Section 4 — Debugging**

Compare `section4_buggy.py` with `section4_fixed.py`: unsafe patterns, inefficient algorithms, and loading entire files into memory.

## Error handling (Sections 1–2)

- **Section 1**: Missing file, directory instead of file, permissions, UTF-8 issues, missing columns, invalid `name` / `category` / `price` / `stock` per row (`CSVProductError` and `FileNotFoundError` where appropriate).
- **Section 2**: Typed exceptions (`UnknownProductError`, `InsufficientStockError`, `InvalidProductDataError`, etc.) for clearer control flow than generic `ValueError`/`KeyError` alone.

## License

Use and adapt for hiring exercises or learning as needed.
