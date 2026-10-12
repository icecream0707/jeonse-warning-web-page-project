from datetime import date

from load_trades import recent_months


def test_recent_months_counts_back_across_the_year_boundary():
    assert list(recent_months(3, date(2026, 1, 15))) == ["202601", "202512", "202511"]


def test_24_recent_months_are_distinct_and_start_with_this_month():
    months = list(recent_months(24, date(2026, 10, 12)))
    assert len(set(months)) == 24
    assert months[0] == "202610" and months[-1] == "202411"
