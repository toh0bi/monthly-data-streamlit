import pandas as pd
import pytest

from src.logic.analytics import (
    calculate_formula_monthly,
    calculate_formula_yearly_stats,
    extract_formula_variables,
    validate_formula,
)


def monthly_df(values: dict[str, float]) -> pd.DataFrame:
    """Builds a minimal monthly DataFrame as produced by calculate_monthly_consumption."""
    rows = []
    for m_str, val in values.items():
        dt = pd.to_datetime(f"{m_str}-01") + pd.offsets.MonthEnd(0)
        rows.append({'date': dt, 'consumption': val, 'month_str': m_str})
    return pd.DataFrame(rows)


class TestExtractFormulaVariables:
    def test_basic_extraction_order_and_dedup(self):
        assert extract_formula_variables("[A] + 2*[B] - [A]") == ["A", "B"]

    def test_strips_whitespace(self):
        assert extract_formula_variables("[ Main Meter ] + [PV]") == ["Main Meter", "PV"]

    def test_empty_formula(self):
        assert extract_formula_variables("") == []
        assert extract_formula_variables(None) == []


class TestValidateFormula:
    AVAILABLE = ["A", "B", "Main Meter"]

    def test_valid_simple(self):
        ok, msg = validate_formula("[A] + [B]", self.AVAILABLE)
        assert ok, msg

    def test_valid_with_factor_and_parens(self):
        ok, _ = validate_formula("2 * ([A] - [B]) / 3", self.AVAILABLE)
        assert ok

    def test_valid_implicit_multiplication(self):
        ok, _ = validate_formula("2[A]", self.AVAILABLE)
        assert ok

    def test_valid_decimal_comma(self):
        ok, _ = validate_formula("1,5 * [A]", self.AVAILABLE)
        assert ok

    def test_empty_formula_invalid(self):
        ok, _ = validate_formula("", self.AVAILABLE)
        assert not ok

    def test_requires_at_least_one_variable(self):
        ok, _ = validate_formula("1 + 2", self.AVAILABLE)
        assert not ok

    def test_unknown_series(self):
        ok, msg = validate_formula("[Unknown]", self.AVAILABLE)
        assert not ok
        assert "Unknown" in msg

    def test_self_reference_forbidden(self):
        ok, _ = validate_formula("[A] + 1", self.AVAILABLE, self_name="A")
        assert not ok

    def test_broken_syntax(self):
        ok, _ = validate_formula("[A] + ", self.AVAILABLE)
        assert not ok

    def test_power_operator_not_allowed(self):
        ok, _ = validate_formula("[A] ** 2", self.AVAILABLE)
        assert not ok

    def test_code_injection_blocked(self):
        ok, _ = validate_formula("__import__('os').system('x') + [A]", self.AVAILABLE)
        assert not ok


class TestCalculateFormulaMonthly:
    def test_subtraction_on_common_months_only(self):
        sources = {
            "A": monthly_df({"2024-01": 100.0, "2024-02": 120.0}),
            "B": monthly_df({"2024-02": 20.0, "2024-03": 30.0}),
        }
        result = calculate_formula_monthly("[A] - [B]", sources)

        assert list(result['month_str']) == ["2024-02"]
        assert result.loc[0, 'consumption'] == pytest.approx(100.0)
        assert result.loc[0, 'year'] == 2024
        assert result.loc[0, 'month_name'] == 'Feb'

    def test_zero_values_are_preserved(self):
        sources = {
            "A": monthly_df({"2024-01": 0.0}),
            "B": monthly_df({"2024-01": 5.0}),
        }
        result = calculate_formula_monthly("[A] + [B]", sources)

        assert result.loc[0, 'consumption'] == pytest.approx(5.0)

    def test_division_by_zero_months_are_dropped(self):
        sources = {
            "A": monthly_df({"2024-01": 10.0, "2024-02": 10.0}),
            "B": monthly_df({"2024-01": 0.0, "2024-02": 2.0}),
        }
        result = calculate_formula_monthly("[A] / [B]", sources)

        assert list(result['month_str']) == ["2024-02"]
        assert result.loc[0, 'consumption'] == pytest.approx(5.0)

    def test_missing_source_series_returns_empty(self):
        result = calculate_formula_monthly("[A] + [B]", {"A": monthly_df({"2024-01": 1.0})})
        assert result.empty

    def test_implicit_multiplication_and_decimal_comma(self):
        sources = {"A": monthly_df({"2024-01": 10.0})}
        result = calculate_formula_monthly("1,5[A]", sources)

        assert result.loc[0, 'consumption'] == pytest.approx(15.0)


class TestCalculateFormulaYearlyStats:
    def test_empty(self):
        assert calculate_formula_yearly_stats(pd.DataFrame()).empty
        assert calculate_formula_yearly_stats(None).empty

    def test_single_month_stats(self):
        sources = {"A": monthly_df({"2024-01": 31.0})}
        monthly = calculate_formula_monthly("[A]", sources)
        stats = calculate_formula_yearly_stats(monthly)

        row = stats.iloc[0]
        assert row['year'] == 2024
        assert row['data_points'] == 1
        assert row['total_consumption'] == pytest.approx(31.0)
        assert row['avg_monthly'] == pytest.approx(31.0)
        # January has 31 calendar days -> avg daily is 1.0
        assert row['avg_daily'] == pytest.approx(1.0)
