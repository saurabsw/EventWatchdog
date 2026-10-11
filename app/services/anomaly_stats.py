import math
import statistics
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime


class StatisticalModelBaseline:
    """
    Computes statistical baselines and prediction bounds for a 1D time-series.
    Supported strategies:
    1. 'robust_mad': Median and Median Absolute Deviation (MAD), robust against historical outliers.
    2. 'rolling_zscore': Mean and Standard Deviation.

    Limitations:
    - Assumes unimodal, stationary or quasi-stationary distributions across the configured history window.
    - Not a neural/deep-learning forecasting model. It does not learn arbitrary non-linear trend dynamics or multi-seasonality.
    """

    @staticmethod
    def clean_and_sort_samples(raw_samples: List[Tuple[int, float]]) -> List[float]:
        """
        Deduplicates timestamps (keeping the latest), drops NaN/Inf, and returns sorted numeric values.
        """
        if not raw_samples:
            return []

        # Sort by timestamp
        raw_samples.sort(key=lambda s: s[0])

        deduped_map: Dict[int, float] = {}
        for ts, val in raw_samples:
            if math.isnan(val) or math.isinf(val):
                continue
            deduped_map[ts] = val

        # Sorted by timestamp order
        return [deduped_map[ts] for ts in sorted(deduped_map.keys())]

    @classmethod
    def fit(
        cls,
        values: List[float],
        strategy: str = "robust_mad",
        multiplier: float = 3.0,
        min_samples: int = 50
    ) -> Dict[str, Any]:
        """
        Fits baseline on cleaned numerical series values.
        Returns:
            {
                "baseline_expected": float,
                "scale_factor": float, # stddev or MAD
                "upper_bound": float,
                "lower_bound": float,
                "sample_count": int,
                "status": "TRAINED",
                "message": str
            }
        """
        if len(values) < min_samples:
            raise ValueError(f"Insufficient history: {len(values)} samples found (minimum required: {min_samples})")

        n = len(values)

        if strategy == "robust_mad":
            median_val = statistics.median(values)
            deviations = [abs(x - median_val) for x in values]
            mad = statistics.median(deviations)
            # Consistency scale factor for normal distribution: ~1.4826
            scale = mad * 1.4826

            # Handle constant or zero-variance series gracefully with epsilon noise floor
            if scale == 0:
                scale = max(0.01, abs(median_val) * 0.05)

            upper = median_val + (multiplier * scale)
            lower = max(0.0, median_val - (multiplier * scale))

            return {
                "baseline_expected": float(median_val),
                "scale_factor": float(scale),
                "upper_bound": float(upper),
                "lower_bound": float(lower),
                "sample_count": n,
                "status": "TRAINED",
                "message": f"Fitted robust MAD baseline over {n} observations"
            }

        elif strategy == "rolling_zscore":
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if n > 1 else 0.0

            if std_val == 0:
                std_val = max(0.01, abs(mean_val) * 0.05)

            upper = mean_val + (multiplier * std_val)
            lower = max(0.0, mean_val - (multiplier * std_val))

            return {
                "baseline_expected": float(mean_val),
                "scale_factor": float(std_val),
                "upper_bound": float(upper),
                "lower_bound": float(lower),
                "sample_count": n,
                "status": "TRAINED",
                "message": f"Fitted rolling zscore baseline over {n} observations"
            }

        else:
            raise ValueError(f"Unsupported model strategy '{strategy}'. Use 'robust_mad' or 'rolling_zscore'.")
