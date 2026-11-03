import pandas as pd
import pytest

from src.data.models import MeterReading
from src.logic.analytics import (
    calculate_monthly_consumption,
    calculate_yearly_stats,
    process_readings,
)


def make_readings(data: list[tuple[str, float]], meter_type: str = "electricity") -> list[MeterReading]:
    return [MeterReading(meter_type=meter_type, meter_reading=v, reading_date=d) for d, v in data]


class TestProcessReadings:
    def test_empty(self):
        assert process_readings([]).empty

    def test_basic_diffs(self):
        readings = make_readings([("2024-01-01", 100.0), ("2024-02-01", 200.0)])
        df = process_readings(readings)

        assert len(df) == 2
        assert df.loc[1, 'reading_diff'] == 100.0
        assert df.loc[1, 'days_diff'] == 31
        assert df.loc[1, 'daily_avg'] == pytest.approx(100.0 / 31)

    def test_sorts_unsorted_input(self):
        readings = make_readings([("2024-02-01", 200.0), ("2024-01-01", 100.0)])
        df = process_readings(readings)

        assert list(df['meter_reading']) == [100.0, 200.0]

    def test_same_day_duplicates_keep_last(self):
        readings = make_readings([("2024-01-01", 100.0), ("2024-01-01", 150.0), ("2024-02-01", 250.0)])
        df = process_readings(readings)

        assert len(df) == 2
        assert df.loc[0, 'meter_reading'] == 150.0
        assert df.loc[1, 'reading_diff'] == 100.0

    def test_meter_reset_clamped_to_zero(self):
        readings = make_readings([("2024-01-01", 100.0), ("2024-02-01", 50.0)])
        df = process_readings(readings)

        assert df.loc[1, 'reading_diff'] == 0.0


class TestMonthlyConsumptionDifferenceMode:
    def test_empty_and_single_reading(self):
        assert calculate_monthly_consumption([]).empty
        assert calculate_monthly_consumption(make_readings([("2024-01-01", 100.0)])).empty

    def test_two_readings_one_month_apart(self):
        readings = make_readings([("2024-01-01", 100.0), ("2024-02-01", 200.0)])
        result = calculate_monthly_consumption(readings, eval_mode='difference')

        # Jan is covered on 30 days (Jan 2 - Jan 31) at a rate of 100/31 per day.
        # Feb has only 1 covered day (< 20) and must be excluded.
        assert list(result['month_str']) == ['2024-01']
        assert result.loc[0, 'consumption'] == pytest.approx(30 * 100.0 / 31)
        assert result.loc[0, 'year'] == 2024
        assert result.loc[0, 'month_name'] == 'Jan'

    def test_months_with_too_few_covered_days_are_excluded(self):
        # Only 10 days covered within January -> below MIN_COVERED_DAYS_PER_MONTH
        readings = make_readings([("2024-01-05", 10.0), ("2024-01-15", 20.0)])
        result = calculate_monthly_consumption(readings, eval_mode='difference')

        assert result.empty

    def test_meter_reset_produces_zero_consumption(self):
        readings = make_readings([("2024-01-01", 100.0), ("2024-02-01", 50.0)])
        result = calculate_monthly_consumption(readings, eval_mode='difference')

        assert list(result['month_str']) == ['2024-01']
        assert result.loc[0, 'consumption'] == 0.0


class TestMonthlyConsumptionAbsoluteMode:
    def test_constant_value_interpolation(self):
        readings = make_readings([("2024-01-01", 70.0), ("2024-03-31", 70.0)])
        result = calculate_monthly_consumption(readings, eval_mode='absolute')

        assert list(result['month_str']) == ['2024-01', '2024-02', '2024-03']
        assert all(c == pytest.approx(70.0) for c in result['consumption'])

    def test_linear_interpolation_monthly_mean(self):
        # 0 on Jan 1 rising linearly to 30 on Jan 31 -> values 0..30, mean 15
        readings = make_readings([("2024-01-01", 0.0), ("2024-01-31", 30.0)])
        result = calculate_monthly_consumption(readings, eval_mode='absolute')

        assert list(result['month_str']) == ['2024-01']
        assert result.loc[0, 'consumption'] == pytest.approx(15.0)

    def test_single_reading_absolute(self):
        readings = make_readings([("2024-01-15", 42.0)])
        result = calculate_monthly_consumption(readings, eval_mode='absolute')

        assert list(result['month_str']) == ['2024-01']
        assert result.loc[0, 'consumption'] == pytest.approx(42.0)


class TestYearlyStats:
    def test_empty(self):
        assert calculate_yearly_stats([], pd.DataFrame()).empty

    def test_difference_mode_stats(self):
        readings = make_readings([("2024-01-01", 100.0), ("2024-02-01", 200.0)])
        monthly = calculate_monthly_consumption(readings, eval_mode='difference')
        stats = calculate_yearly_stats(readings, monthly, eval_mode='difference')

        assert len(stats) == 1
        row = stats.iloc[0]
        assert row['year'] == 2024
        assert row['data_points'] == 2
        expected_total = 30 * 100.0 / 31
        assert row['total_consumption'] == pytest.approx(expected_total)
        assert row['avg_monthly'] == pytest.approx(expected_total)
        # 30 covered days in January -> daily average equals the meter rate
        assert row['avg_daily'] == pytest.approx(100.0 / 31)

    def test_absolute_mode_stats_use_mean_and_min_max(self):
        readings = make_readings([("2024-01-01", 60.0), ("2024-03-31", 80.0)])
        monthly = calculate_monthly_consumption(readings, eval_mode='absolute')
        stats = calculate_yearly_stats(readings, monthly, eval_mode='absolute')

        row = stats.iloc[0]
        assert row['year'] == 2024
        assert row['min_value'] == 60.0
        assert row['max_value'] == 80.0
        assert row['total_consumption'] == pytest.approx(monthly['consumption'].mean())
