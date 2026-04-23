from datetime import datetime, timezone, timedelta

from app.services.filter_engine import matches, FilterCriteria


NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)


def test_matches_happy_path():
    assert matches(NOW - timedelta(hours=24), 15000.0, dex="raydium_amm", now=NOW) is True


def test_rejects_too_old():
    assert matches(NOW - timedelta(hours=72, minutes=1), 50000.0, now=NOW) is False


def test_accepts_just_under_72h():
    assert matches(NOW - timedelta(hours=71, minutes=59), 50000.0, now=NOW) is True


def test_rejects_low_liquidity():
    assert matches(NOW - timedelta(hours=1), 9999.99, now=NOW) is False


def test_rejects_equal_liquidity():
    # spec: liquidity > 10000, strict
    assert matches(NOW - timedelta(hours=1), 10000.0, now=NOW) is False


def test_accepts_just_above():
    assert matches(NOW - timedelta(hours=1), 10000.01, now=NOW) is True


def test_dex_filter():
    c = FilterCriteria(dex="raydium_amm")
    assert matches(NOW - timedelta(hours=1), 50000, dex="pumpfun_bonding", criteria=c, now=NOW) is False
    assert matches(NOW - timedelta(hours=1), 50000, dex="raydium_amm", criteria=c, now=NOW) is True


def test_none_values():
    assert matches(None, 50000, now=NOW) is False
    assert matches(NOW, None, now=NOW) is False
