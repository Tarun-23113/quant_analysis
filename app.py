from dashboard import Dashboard
from alerts import AlertSystem
from analytics import QuantAnalytics
from storage import DataStore
from ingestion import BinanceDataStream
import asyncio
import threading
import time
import pandas as pd
import streamlit as st
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


# Global variables for data sharing
data_store = None
analytics = None
alert_system = None
symbols = ['BTCUSDT', 'ETHUSDT']
timeframes = ['1s', '1min', '5min']


class QuantApp:
    def __init__(self):
        """Initialize the quantitative application"""
        global data_store, analytics, alert_system

        # Initialize components if not already done
        if data_store is None:
            data_store = DataStore()
        if analytics is None:
            analytics = QuantAnalytics()
        if alert_system is None:
            alert_system = AlertSystem()
            self._setup_default_alerts()

        # Control flags
        self.running = False
        self.data_thread = None

    def _setup_default_alerts(self):
        """Setup default alert conditions"""
        def zscore_alert(data):
            if len(data) == 0 or 'zscore' not in data.columns:
                return False
            latest_zscore = data['zscore'].iloc[-1] if len(data) > 0 else 0
            return abs(latest_zscore) > 2.0

        # Add alert only if not already added
        if not alert_system.get_active_alerts():
            alert_system.add_alert("Z-Score Alert (>2)", zscore_alert)

    async def _handle_tick_data(self, tick_data):
        """
        Handle incoming tick data

        Args:
            tick_data: Dictionary with tick information
        """
        global data_store
        # Store tick data
        data_store.add_tick(tick_data)

        # Resample data periodically
        data_store.resample_data()

    def _data_collection_loop(self):
        """Run data collection in a separate thread"""
        global symbols

        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Create data stream
        data_stream = BinanceDataStream(symbols)
        data_stream.add_callback(self._handle_tick_data)

        try:
            loop.run_until_complete(data_stream.start_streams())
        except Exception as e:
            print(f"Error in data collection loop: {e}")
        finally:
            loop.close()

    def start_data_collection(self):
        """Start data collection in a background thread"""
        global data_store
        if not self.running:
            self.running = True
            data_thread = threading.Thread(
                target=self._data_collection_loop, daemon=True)
            data_thread.start()
            self.data_thread = data_thread
            print("Data collection started")

    def stop_data_collection(self):
        """Stop data collection"""
        self.running = False
        print("Data collection stopped")

    def run_dashboard(self):
        """Run the Streamlit dashboard"""
        global data_store, analytics, alert_system, symbols, timeframes

        # Initialize app
        dashboard = Dashboard()

        # Set page config
        st.set_page_config(
            page_title="Quant Analytics Dashboard",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Render dashboard header
        dashboard.render_header()

        # Start data collection if not already running
        if not self.running:
            self.start_data_collection()
            st.info(
                "Starting data collection... Please wait a moment for data to populate.")

        # Render controls
        selected_symbol, selected_timeframe, rolling_window = dashboard.render_controls(
            symbols, timeframes
        )

        # Get data for selected symbol and timeframe
        try:
            resampled_data = data_store.get_resampled_data(
                selected_timeframe, selected_symbol)
        except Exception as e:
            resampled_data = pd.DataFrame()
            print(f"Error getting resampled data: {e}")

        # Calculate analytics
        stats = {}
        spread_data = pd.Series(dtype=float)
        zscore_data = pd.Series(dtype=float)
        correlation_data = pd.Series(dtype=float)
        adf_results = {}

        if not resampled_data.empty and 'close' in resampled_data.columns:
            # Get price data for analytics
            price_data = pd.DataFrame({'price': resampled_data['close']})
            stats = analytics.calculate_price_statistics(price_data)

            # Calculate spread and z-score if we have multiple symbols
            if len(symbols) >= 2:
                try:
                    symbol1_data = data_store.get_resampled_data(
                        selected_timeframe, symbols[0])
                    symbol2_data = data_store.get_resampled_data(
                        selected_timeframe, symbols[1])

                    if not symbol1_data.empty and not symbol2_data.empty and 'close' in symbol1_data.columns and 'close' in symbol2_data.columns:
                        # Align data lengths
                        min_len = min(len(symbol1_data), len(symbol2_data))
                        if min_len > 1:  # Need at least 2 points for calculations
                            asset1_prices = symbol1_data['close'].tail(min_len)
                            asset2_prices = symbol2_data['close'].tail(min_len)

                            # Reset indices to align data
                            asset1_prices = asset1_prices.reset_index(
                                drop=True)
                            asset2_prices = asset2_prices.reset_index(
                                drop=True)

                            # Calculate hedge ratio and spread
                            try:
                                hedge_ratio = analytics.calculate_hedge_ratio(
                                    asset1_prices, asset2_prices)
                                spread_data = analytics.calculate_spread(
                                    asset1_prices, asset2_prices, hedge_ratio)

                                # Calculate z-score
                                if len(spread_data) >= rolling_window and len(spread_data) > 0:
                                    zscore_data = analytics.calculate_zscore(
                                        spread_data, rolling_window)

                                # Calculate correlation
                                if len(asset1_prices) >= rolling_window:
                                    correlation_data = analytics.calculate_correlation(
                                        asset1_prices, asset2_prices, rolling_window
                                    )
                            except Exception as e:
                                print(f"Analytics calculation error: {e}")
                except Exception as e:
                    print(f"Error getting symbol data: {e}")

        # Render charts
        dashboard.render_price_chart(resampled_data, selected_symbol)

        if not spread_data.empty and len(spread_data) > 1:
            # Ensure index is datetime for proper plotting
            if not isinstance(spread_data.index, pd.DatetimeIndex):
                spread_data.index = pd.date_range(
                    start=pd.Timestamp.now(), periods=len(spread_data), freq='1min')
            dashboard.render_spread_chart(spread_data)

        if not zscore_data.empty and len(zscore_data) > 1:
            # Ensure index is datetime for proper plotting
            if not isinstance(zscore_data.index, pd.DatetimeIndex):
                zscore_data.index = pd.date_range(
                    start=pd.Timestamp.now(), periods=len(zscore_data), freq='1min')
            dashboard.render_zscore_chart(zscore_data)

        if not correlation_data.empty and len(correlation_data) > 1:
            # Ensure index is datetime for proper plotting
            if not isinstance(correlation_data.index, pd.DatetimeIndex):
                correlation_data.index = pd.date_range(
                    start=pd.Timestamp.now(), periods=len(correlation_data), freq='1min')
            dashboard.render_correlation_chart(correlation_data)

        # Render statistics
        dashboard.render_stats_table(stats)

        # Render alert controls
        alert_threshold, alert_active = dashboard.render_alert_controls()

        # Check alerts if active
        triggered_alerts = []
        if alert_active and not zscore_data.empty and len(zscore_data) > 0:
            # Create temporary DataFrame for alert checking
            alert_data = pd.DataFrame({'zscore': zscore_data})
            triggered_alerts = alert_system.check_alerts(
                alert_data, selected_symbol)

        # Render alerts
        dashboard.render_alerts(triggered_alerts)

        # ADF Test section
        st.subheader("Statistical Tests")
        if st.button("Run ADF Test on Spread"):
            if not spread_data.empty:
                adf_results = analytics.perform_adf_test(spread_data)
                dashboard.render_adf_results(adf_results)
            else:
                st.warning("Not enough data for ADF test")

        # Render export controls
        export_price, export_analytics = dashboard.render_export_controls()

        if export_price:
            filename = f"price_data_{selected_symbol}_{selected_timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            resampled_data.to_csv(filename, index=False)
            st.success(f"Price data exported to {filename}")

        if export_analytics:
            # Create analytics summary
            analytics_summary = pd.DataFrame([{
                'symbol': selected_symbol,
                'timeframe': selected_timeframe,
                'mean_price': stats.get('mean_price', 0),
                'std_price': stats.get('std_price', 0),
                'mean_return': stats.get('mean_return', 0),
                'std_return': stats.get('std_return', 0),
                'latest_zscore': zscore_data.iloc[-1] if not zscore_data.empty else 0,
                'latest_correlation': correlation_data.iloc[-1] if not correlation_data.empty else 0
            }])
            filename = f"analytics_{selected_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            analytics_summary.to_csv(filename, index=False)
            st.success(f"Analytics data exported to {filename}")

        # Auto-refresh
        if st.checkbox("Auto-refresh", value=True):
            st.rerun()


def main():
    """Main application entry point"""
    # Create app instance
    app = QuantApp()

    # Run dashboard
    app.run_dashboard()


if __name__ == "__main__":
    main()
