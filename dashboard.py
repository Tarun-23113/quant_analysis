import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np


class Dashboard:
    def __init__(self):
        """Initialize dashboard"""
        pass

    def render_header(self):
        """Render dashboard header"""
        st.title("Quantitative Analytics Dashboard")
        st.markdown("""
        Real-time cryptocurrency analytics with statistical measures and alerts.
        """)

    def render_controls(self, symbols: list, timeframes: list) -> tuple:
        """
        Render control panel

        Args:
            symbols: List of available symbols
            timeframes: List of available timeframes

        Returns:
            Tuple of (selected_symbol, selected_timeframe, rolling_window)
        """
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_symbol = st.selectbox("Select Symbol", symbols, index=0)

        with col2:
            selected_timeframe = st.selectbox(
                "Select Timeframe", timeframes, index=1)

        with col3:
            rolling_window = st.number_input(
                "Rolling Window", min_value=5, max_value=100, value=20)

        return selected_symbol, selected_timeframe, rolling_window

    def render_price_chart(self, data: pd.DataFrame, symbol: str):
        """
        Render price chart

        Args:
            data: DataFrame with OHLCV data
            symbol: Symbol being displayed
        """
        if data.empty:
            st.warning("No price data available")
            return

        fig = go.Figure(data=[go.Candlestick(
            x=data['timestamp'],
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name=symbol
        )])

        fig.update_layout(
            title=f"{symbol} Price Chart",
            xaxis_title="Time",
            yaxis_title="Price (USDT)",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_spread_chart(self, spread_data: pd.Series):
        """
        Render spread chart

        Args:
            spread_data: Series with spread values
        """
        if spread_data.empty:
            st.warning("No spread data available")
            return

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=spread_data.index,
            y=spread_data.values,
            mode='lines',
            name='Spread'
        ))

        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="red")

        fig.update_layout(
            title="Spread Between Assets",
            xaxis_title="Time",
            yaxis_title="Spread",
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_zscore_chart(self, zscore_data: pd.Series):
        """
        Render z-score chart

        Args:
            zscore_data: Series with z-score values
        """
        if zscore_data.empty:
            st.warning("No z-score data available")
            return

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=zscore_data.index,
            y=zscore_data.values,
            mode='lines',
            name='Z-Score'
        ))

        # Add threshold lines
        fig.add_hline(y=2, line_dash="dash", line_color="orange",
                      annotation_text="Upper Threshold")
        fig.add_hline(y=-2, line_dash="dash", line_color="orange",
                      annotation_text="Lower Threshold")
        fig.add_hline(y=0, line_dash="solid", line_color="gray")

        fig.update_layout(
            title="Z-Score Analysis",
            xaxis_title="Time",
            yaxis_title="Z-Score",
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_correlation_chart(self, correlation_data: pd.Series):
        """
        Render correlation chart

        Args:
            correlation_data: Series with correlation values
        """
        if correlation_data.empty:
            st.warning("No correlation data available")
            return

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=correlation_data.index,
            y=correlation_data.values,
            mode='lines',
            name='Correlation'
        ))

        # Add benchmark lines
        fig.add_hline(y=0.8, line_dash="dot", line_color="green",
                      annotation_text="Strong Correlation")
        fig.add_hline(y=0, line_dash="solid", line_color="gray")
        fig.add_hline(y=-0.8, line_dash="dot", line_color="green",
                      annotation_text="Strong Negative Correlation")

        fig.update_layout(
            title="Rolling Correlation",
            xaxis_title="Time",
            yaxis_title="Correlation",
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

    def render_stats_table(self, stats: dict):
        """
        Render statistics table

        Args:
            stats: Dictionary with statistics
        """
        if not stats:
            st.warning("No statistics available")
            return

        st.subheader("Summary Statistics")

        # Convert stats to DataFrame for display
        stats_df = pd.DataFrame([stats])
        st.dataframe(stats_df.round(6), use_container_width=True)

    def render_alert_controls(self):
        """
        Render alert controls

        Returns:
            Tuple of (alert_threshold, alert_active)
        """
        st.subheader("Alert Configuration")

        col1, col2 = st.columns(2)

        with col1:
            alert_threshold = st.number_input(
                "Z-Score Threshold", min_value=0.1, max_value=10.0, value=2.0, step=0.1)

        with col2:
            alert_active = st.checkbox("Enable Alerts", value=True)

        return alert_threshold, alert_active

    def render_alerts(self, triggered_alerts: list):
        """
        Render triggered alerts

        Args:
            triggered_alerts: List of triggered alerts
        """
        if triggered_alerts:
            st.subheader("Recent Alerts")
            for alert in triggered_alerts[-5:]:  # Show last 5 alerts
                st.warning(
                    f"🚨 {alert['name']} triggered for {alert['symbol']} at {alert['timestamp']}")
        else:
            st.info("No alerts triggered")

    def render_export_controls(self):
        """
        Render export controls

        Returns:
            Boolean indicating if export was requested
        """
        st.subheader("Data Export")
        col1, col2 = st.columns(2)

        with col1:
            export_price_data = st.button("Export Price Data")

        with col2:
            export_analytics = st.button("Export Analytics")

        return export_price_data, export_analytics

    def render_adf_results(self, adf_results: dict):
        """
        Render ADF test results

        Args:
            adf_results: Dictionary with ADF test results
        """
        if not adf_results:
            return

        st.subheader("ADF Test Results")

        if 'error' in adf_results:
            st.error(f"ADF Test Error: {adf_results['error']}")
        else:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("ADF Statistic",
                          f"{adf_results['adf_statistic']:.6f}")

            with col2:
                st.metric("P-Value", f"{adf_results['p_value']:.6f}")

            with col3:
                is_stationary = adf_results['is_stationary']
                status = "Stationary" if is_stationary else "Non-Stationary"
                st.metric("Result", status,
                          delta="✓" if is_stationary else "✗")


# Example usage
if __name__ == "__main__":
    # Test the dashboard rendering
    dashboard = Dashboard()

    # Create sample data
    dates = pd.date_range('2023-01-01', periods=100, freq='1min')
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.rand(100) * 1000 + 49000,
        'high': np.random.rand(100) * 1000 + 50000,
        'low': np.random.rand(100) * 1000 + 48000,
        'close': np.random.rand(100) * 1000 + 49500,
        'volume': np.random.rand(100) * 100
    })

    # Render components
    dashboard.render_header()
    symbol, timeframe, window = dashboard.render_controls(
        ['BTCUSDT', 'ETHUSDT'], ['1s', '1min', '5min'])

    # Render charts
    dashboard.render_price_chart(sample_data, 'BTCUSDT')
