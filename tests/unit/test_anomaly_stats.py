import math
import pytest
from app.services.anomaly_stats import StatisticalModelBaseline


def test_clean_and_sort_samples():
    raw = [
        (100, 50.0),
        (105, float("nan")),
        (110, 52.0),
        (110, 53.0),  # duplicate timestamp
        (115, float("inf")),
        (90, 48.0)    # out of order
    ]
    cleaned = StatisticalModelBaseline.clean_and_sort_samples(raw)
    assert len(cleaned) == 3
    # Timestamps 90, 100, 110 (latest val for 110 is 53.0)
    assert cleaned == [48.0, 50.0, 53.0]


def test_insufficient_samples_raises_error():
    values = [10.0] * 30  # less than minimum 50
    with pytest.raises(ValueError, match="Insufficient history"):
        StatisticalModelBaseline.fit(values, min_samples=50)


def test_fit_robust_mad_strategy():
    # 100 normal observations around 100.0, plus 5 outliers
    values = [100.0 + (i % 5) for i in range(100)]
    values[10] = 500.0  # outlier

    res = StatisticalModelBaseline.fit(values, strategy="robust_mad", multiplier=3.0, min_samples=50)
    assert res["status"] == "TRAINED"
    assert 99.0 <= res["baseline_expected"] <= 103.0
    assert res["upper_bound"] > res["baseline_expected"]
    assert res["lower_bound"] < res["baseline_expected"]
    assert res["sample_count"] == 100


def test_fit_rolling_zscore_strategy():
    values = [50.0 + (i % 10) for i in range(80)]
    res = StatisticalModelBaseline.fit(values, strategy="rolling_zscore", multiplier=3.0, min_samples=50)
    assert res["status"] == "TRAINED"
    assert 53.0 <= res["baseline_expected"] <= 56.0
    assert res["upper_bound"] > res["baseline_expected"]


def test_constant_series_handled_with_epsilon_floor():
    # Series with zero variance (all identical numbers)
    values = [42.0] * 60
    res = StatisticalModelBaseline.fit(values, strategy="robust_mad", multiplier=3.0, min_samples=50)
    assert res["status"] == "TRAINED"
    # Scale factor should not be 0
    assert res["scale_factor"] > 0
    assert res["upper_bound"] > 42.0
    assert res["lower_bound"] < 42.0
