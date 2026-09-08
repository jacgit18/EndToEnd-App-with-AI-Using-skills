from decimal import Decimal

from app.routers.transactions import dedupe_hash


def test_dedupe_hash_is_stable_and_normalizes_description() -> None:
    a = dedupe_hash("2026-01-01", Decimal("12.34"), "  Coffee Shop ")
    b = dedupe_hash("2026-01-01", "12.34", "coffee shop")
    assert a == b
    assert len(a) == 64


def test_dedupe_hash_differs_on_amount() -> None:
    assert dedupe_hash("2026-01-01", Decimal("12.34"), "x") != dedupe_hash(
        "2026-01-01", Decimal("12.35"), "x"
    )


def test_dedupe_hash_normalizes_amount_precision() -> None:
    assert dedupe_hash("2026-01-01", Decimal("12.3"), "x") == dedupe_hash(
        "2026-01-01", Decimal("12.30"), "x"
    )
