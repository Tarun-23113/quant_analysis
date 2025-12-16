import pandas as pd
import numpy as np
from statsmodels.regression.linear_model import OLS
from statsmodels.tsa.stattools import adfuller
import warnings


class QuantAnalytics:
    def __init__(self):
        """Initialize analytics engine"""
        pass

    def calculate_price_statistics(self, data: pd.DataFrame) -> dict:
        """
        Calculate basic price statistics

        Args:
            data: DataFrame with 'price' column

        Returns:
            Dictionary with statistics
        """
        if data.empty or 'price' not in data.columns:
            return {}

        prices = data['price'].dropna()
        if len(prices) == 0:
            return {}

        # Calculate returns
        returns = prices.pct_change().dropna()

        stats = {
            'mean_price': float(prices.mean()) if not prices.empty else 0,
            'std_price': float(prices.std()) if not prices.empty else 0,
            'mean_return': float(returns.mean()) if not returns.empty else 0,
            'std_return': float(returns.std()) if not returns.empty else 0,
            'min_price': float(prices.min()) if not prices.empty else 0,
            'max_price': float(prices.max()) if not prices.empty else 0,
            'count': int(len(prices))
        }

        return stats

    def calculate_hedge_ratio(self, asset1_prices: pd.Series, asset2_prices: pd.Series) -> float:
        """
        Calculate hedge ratio using OLS regression
        Hedge ratio = β where asset1 = α + β * asset2 + ε

        Formula: β = Cov(asset1, asset2) / Var(asset2)

        Args:
            asset1_prices: Prices of first asset
            asset2_prices: Prices of second asset

        Returns:
            Hedge ratio (β coefficient)
        """
        # Align data by index
        df = pd.DataFrame(
            {'asset1': asset1_prices, 'asset2': asset2_prices}).dropna()

        if len(df) < 2:
            return 0.0

        try:
            # Use statsmodels OLS
            X = df['asset2']
            y = df['asset1']

            # Add constant
            X = pd.concat([pd.Series([1]*len(X), index=X.index), X], axis=1)
            X.columns = ['const', 'asset2']

            # Fit OLS model
            model = OLS(y, X).fit()
            hedge_ratio = model.params['asset2']  # β coefficient
            return float(hedge_ratio)
        except Exception as e:
            # Fallback to manual calculation
            try:
                cov = np.cov(df['asset1'], df['asset2'])[0, 1]
                var = np.var(df['asset2'])
                return float(cov / var) if var != 0 else 0.0
            except:
                return 0.0

    def calculate_spread(self, asset1_prices: pd.Series, asset2_prices: pd.Series, hedge_ratio: float) -> pd.Series:
        """
        Calculate spread between two assets using hedge ratio
        Spread = asset1 - hedge_ratio * asset2

        Args:
            asset1_prices: Prices of first asset
            asset2_prices: Prices of second asset
            hedge_ratio: Calculated hedge ratio

        Returns:
            Series with spread values
        """
        # Align data by index
        df = pd.DataFrame(
            {'asset1': asset1_prices, 'asset2': asset2_prices}).dropna()

        if df.empty:
            return pd.Series(dtype=float)

        # Calculate spread
        spread = df['asset1'] - hedge_ratio * df['asset2']
        return spread

    def calculate_zscore(self, series: pd.Series, window: int = 20) -> pd.Series:
        """
        Calculate rolling z-score
        Z-score = (x - μ) / σ where μ and σ are rolling mean and std

        Args:
            series: Time series data
            window: Rolling window size

        Returns:
            Series with z-scores
        """
        if len(series) < window or window <= 0:
            return pd.Series([np.nan] * len(series), index=series.index) if len(series) > 0 else pd.Series(dtype=float)

        # Calculate rolling statistics
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()

        # Avoid division by zero
        rolling_std = rolling_std.replace(0, np.nan)

        # Calculate z-score
        zscore = (series - rolling_mean) / rolling_std
        return zscore

    def calculate_correlation(self, asset1_prices: pd.Series, asset2_prices: pd.Series, window: int = 20) -> pd.Series:
        """
        Calculate rolling correlation between two assets

        Args:
            asset1_prices: Prices of first asset
            asset2_prices: Prices of second asset
            window: Rolling window size

        Returns:
            Series with correlation values
        """
        # Align data by index
        df = pd.DataFrame(
            {'asset1': asset1_prices, 'asset2': asset2_prices}).dropna()

        if len(df) < window or window <= 0:
            return pd.Series([np.nan] * len(df), index=df.index) if len(df) > 0 else pd.Series(dtype=float)

        # Calculate rolling correlation
        correlation = df['asset1'].rolling(window=window).corr(df['asset2'])
        return correlation

    def perform_adf_test(self, series: pd.Series) -> dict:
        """
        Perform Augmented Dickey-Fuller test for stationarity

        Args:
            series: Time series data

        Returns:
            Dictionary with ADF test results
        """
        series_clean = series.dropna()

        if len(series_clean) < 10:
            return {'error': 'Insufficient data for ADF test (need at least 10 points)'}

        try:
            # Suppress warnings from statsmodels
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                adf_result = adfuller(series_clean)

            result = {
                'adf_statistic': float(adf_result[0]),
                'p_value': float(adf_result[1]),
                'critical_values': adf_result[4],
                # Stationary if p-value < 0.05
                'is_stationary': bool(adf_result[1] < 0.05)
            }

            return result
        except Exception as e:
            return {'error': f'ADF test failed: {str(e)}'}


# Example usage
if __name__ == "__main__":
    # Test the analytics engine
    analytics = QuantAnalytics()

    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=100, freq='1min')
    asset1_prices = pd.Series(
        50000 + np.cumsum(np.random.randn(100) * 10), index=dates)
    asset2_prices = pd.Series(
        3000 + np.cumsum(np.random.randn(100) * 5), index=dates)

    # Calculate statistics
    data = pd.DataFrame({'price': asset1_prices})
    stats = analytics.calculate_price_statistics(data)
    print("Price Statistics:", stats)

    # Calculate hedge ratio
    hedge_ratio = analytics.calculate_hedge_ratio(asset1_prices, asset2_prices)
    print(f"Hedge Ratio: {hedge_ratio}")

    # Calculate spread
    spread = analytics.calculate_spread(
        asset1_prices, asset2_prices, hedge_ratio)
    print(f"Spread range: {spread.min()} to {spread.max()}")

    # Calculate z-score
    zscore = analytics.calculate_zscore(spread, window=20)
    print(f"Z-score range: {zscore.min()} to {zscore.max()}")

    # Calculate correlation
    correlation = analytics.calculate_correlation(
        asset1_prices, asset2_prices, window=20)
    print(f"Correlation range: {correlation.min()} to {correlation.max()}")

    # Perform ADF test
    adf_result = analytics.perform_adf_test(spread)
    print("ADF Test Result:", adf_result)
