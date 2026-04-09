from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional


class ERPError(Exception):
    """Base class for ERP module errors."""


class UnknownProductError(ERPError, KeyError):
    """Raised when a product name does not exist."""


class InsufficientStockError(ERPError, ValueError):
    """Raised when a sale would drop stock below zero."""


class InvalidProductDataError(ERPError, ValueError):
    """Raised when add_product receives invalid fields."""


@dataclass
class Product:
    name: str
    category: str
    price: Decimal
    stock: int

    def __post_init__(self) -> None:
        if self.stock < 0:
            raise InvalidProductDataError("stock cannot be negative")
        if self.price < 0:
            raise InvalidProductDataError("price cannot be negative")


@dataclass
class SaleLine:
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


def _to_decimal(price: Decimal | float | str, label: str) -> Decimal:
    if isinstance(price, Decimal):
        return price
    try:
        d = Decimal(str(price))
    except InvalidOperation as e:
        raise InvalidProductDataError(f"invalid {label}: {price!r}") from e
    return d


@dataclass
class ERPInventory:
    """Simple in-memory ERP-like inventory and sales tracking."""

    _products: Dict[str, Product] = field(default_factory=dict)
    _sales: List[SaleLine] = field(default_factory=list)
    _total_revenue: Decimal = field(default_factory=lambda: Decimal("0"))

    def add_product(
        self,
        name: str,
        category: str,
        price: Decimal | float | str,
        stock: int,
    ) -> None:
        key = (name or "").strip()
        if not key:
            raise InvalidProductDataError("product name cannot be empty")
        cat = (category or "").strip()
        if not cat:
            raise InvalidProductDataError("category cannot be empty")
        try:
            stock_i = int(stock)
        except (TypeError, ValueError) as e:
            raise InvalidProductDataError(f"invalid stock: {stock!r}") from e
        price_dec = _to_decimal(price, "price")
        if price_dec < 0:
            raise InvalidProductDataError("price cannot be negative")
        if stock_i < 0:
            raise InvalidProductDataError("stock cannot be negative")
        self._products[key] = Product(key, cat, price_dec, stock_i)

    def record_sale(self, product_name: str, quantity: int) -> SaleLine:
        try:
            qty = int(quantity)
        except (TypeError, ValueError) as e:
            raise InvalidProductDataError(f"invalid quantity: {quantity!r}") from e
        if qty <= 0:
            raise InvalidProductDataError("quantity must be positive")
        key = (product_name or "").strip()
        if not key:
            raise InvalidProductDataError("product name cannot be empty")
        if key not in self._products:
            raise UnknownProductError(f"unknown product: {product_name!r}")
        p = self._products[key]
        if p.stock < qty:
            raise InsufficientStockError(
                f"insufficient stock for {key}: have {p.stock}, need {qty}"
            )
        unit = p.price
        line_total = unit * qty
        p.stock -= qty
        line = SaleLine(key, qty, unit, line_total)
        self._sales.append(line)
        self._total_revenue += line_total
        return line

    def summary_report(self) -> Dict[str, Any]:
        stock_by_name = {n: self._products[n].stock for n in self._products}
        return {
            "total_sales_revenue": self._total_revenue,
            "sale_line_count": len(self._sales),
            "remaining_stock_by_product": stock_by_name,
        }

    def get_product(self, name: str) -> Optional[Product]:
        return self._products.get((name or "").strip())

    def list_sale_lines(self) -> List[SaleLine]:
        return list(self._sales)


if __name__ == "__main__":
    inv = ERPInventory()
    inv.add_product("Alpha", "Tools", "19.99", 10)
    inv.add_product("Beta", "Tools", Decimal("5.00"), 20)
    inv.record_sale("Alpha", 2)
    inv.record_sale("Beta", 5)
    print(inv.summary_report())
