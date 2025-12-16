import pandas as pd
import sqlite3
from typing import Dict, List
import threading
import time


class DataStore:
    def __init__(self, db_path: str = None):
        """
        Initialize data store with optional SQLite persistence

        Args:
            db_path: Path to SQLite database file (optional)
        """
        # In-memory storage for tick data
        self.tick_data = pd.DataFrame(
            columns=['timestamp', 'symbol', 'price', 'quantity'])

        # Resampled data storage
        self.resampled_data = {
            '1s': pd.DataFrame(columns=['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']),
            '1min': pd.DataFrame(columns=['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']),
            '5min': pd.DataFrame(columns=['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume'])
        }

        # Lock for thread-safe operations
        self.lock = threading.Lock()

        # SQLite database connection (optional)
        self.db_path = db_path
        self.conn = None
        if db_path:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self._initialize_db()

        # Last resample timestamps
        self.last_resample = {
            '1s': pd.Timestamp.now(),
            '1min': pd.Timestamp.now(),
            '5min': pd.Timestamp.now()
        }

    def _initialize_db(self):
        """Initialize database tables"""
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ticks (
                    timestamp TEXT,
                    symbol TEXT,
                    price REAL,
                    quantity REAL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resampled_1s (
                    timestamp TEXT,
                    symbol TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resampled_1min (
                    timestamp TEXT,
                    symbol TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resampled_5min (
                    timestamp TEXT,
                    symbol TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL
                )
            ''')
            self.conn.commit()

    def add_tick(self, tick_data: Dict):
        """
        Add a new tick to the data store

        Args:
            tick_data: Dictionary with keys 'timestamp', 'symbol', 'price', 'quantity'
        """
        with self.lock:
            # Add to in-memory DataFrame
            new_row = pd.DataFrame([tick_data])
            self.tick_data = pd.concat(
                [self.tick_data, new_row], ignore_index=True)

            # Keep only recent data to prevent memory issues
            if len(self.tick_data) > 10000:
                self.tick_data = self.tick_data.tail(5000)

            # Optionally save to database
            if self.conn:
                new_row.to_sql('ticks', self.conn,
                               if_exists='append', index=False)

    def get_latest_ticks(self, symbol: str = None, limit: int = 1000) -> pd.DataFrame:
        """
        Get latest tick data

        Args:
            symbol: Filter by symbol (optional)
            limit: Number of recent records to return

        Returns:
            DataFrame with tick data
        """
        with self.lock:
            data = self.tick_data.copy()
            if symbol:
                data = data[data['symbol'] == symbol]
            return data.tail(limit)

    def resample_data(self, symbol: str = None):
        """
        Resample tick data to different timeframes

        Args:
            symbol: Resample data for specific symbol (optional, resamples all if None)
        """
        with self.lock:
            # Work with a copy of tick data
            if symbol:
                tick_data = self.tick_data[self.tick_data['symbol'] == symbol].copy(
                )
            else:
                tick_data = self.tick_data.copy()

            if tick_data.empty:
                return

            # Set timestamp as index for resampling
            tick_data = tick_data.set_index('timestamp')

            # Define resampling rules
            resample_rules = {
                '1s': '1s',
                '1min': '1min',
                '5min': '5min'
            }

            # Perform resampling for each timeframe
            for timeframe_key, rule in resample_rules.items():
                try:
                    # Resample using OHLCV (Open, High, Low, Close, Volume)
                    if not tick_data.empty:
                        # Group by symbol and resample price data
                        price_resampled = tick_data.groupby('symbol')['price'].resample(rule).agg({
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last'
                        })

                        # Resample volume data
                        volume_resampled = tick_data.groupby(
                            'symbol')['quantity'].resample(rule).sum()

                        # Combine price and volume data
                        if not price_resampled.empty and not volume_resampled.empty:
                            # Flatten multi-index
                            price_df = price_resampled.reset_index()
                            volume_df = volume_resampled.reset_index()

                            # Merge on timestamp and symbol
                            resampled_df = pd.merge(price_df, volume_df, on=[
                                                    'timestamp', 'symbol'])
                            resampled_df.rename(
                                columns={'quantity': 'volume'}, inplace=True)

                            # Update stored resampled data
                            if self.resampled_data[timeframe_key].empty:
                                self.resampled_data[timeframe_key] = resampled_df
                            else:
                                # Concatenate and remove duplicates
                                combined = pd.concat([
                                    self.resampled_data[timeframe_key],
                                    resampled_df
                                ])
                                self.resampled_data[timeframe_key] = combined.drop_duplicates(
                                    subset=['timestamp', 'symbol'], keep='last'
                                )

                            # Keep only recent data
                            if len(self.resampled_data[timeframe_key]) > 2000:
                                self.resampled_data[timeframe_key] = self.resampled_data[timeframe_key].tail(
                                    1000)

                            # Save to database if enabled
                            if self.conn:
                                table_name = f'resampled_{timeframe_key}'
                                # Only insert new data
                                resampled_df.to_sql(
                                    table_name, self.conn, if_exists='append', index=False)

                except Exception as e:
                    print(f"Error resampling {timeframe_key}: {e}")

            # Update last resample timestamps
            current_time = pd.Timestamp.now()
            for key in self.last_resample:
                self.last_resample[key] = current_time

    def get_resampled_data(self, timeframe: str, symbol: str = None) -> pd.DataFrame:
        """
        Get resampled data for a specific timeframe

        Args:
            timeframe: One of '1s', '1min', '5min'
            symbol: Filter by symbol (optional)

        Returns:
            DataFrame with resampled data
        """
        if timeframe not in self.resampled_data:
            raise ValueError(
                f"Invalid timeframe: {timeframe}. Use '1s', '1min', or '5min'")

        with self.lock:
            data = self.resampled_data[timeframe].copy()
            if symbol and not data.empty:
                data = data[data['symbol'] == symbol]
            # Return empty DataFrame with correct columns if no data
            if data.empty:
                return pd.DataFrame(columns=['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume'])
            return data.sort_values('timestamp').reset_index(drop=True) if 'timestamp' in data.columns else data

    def save_to_csv(self, filepath: str, timeframe: str = None):
        """
        Save data to CSV file

        Args:
            filepath: Path to save CSV file
            timeframe: Timeframe to save ('1s', '1min', '5min') or None for raw ticks
        """
        with self.lock:
            if timeframe:
                data = self.get_resampled_data(timeframe)
            else:
                data = self.tick_data.copy()

            data.to_csv(filepath, index=False)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Example usage
if __name__ == "__main__":
    # Test the data store
    store = DataStore()

    # Add some sample data
    sample_tick = {
        'timestamp': pd.Timestamp.now(),
        'symbol': 'BTCUSDT',
        'price': 50000.0,
        'quantity': 0.1
    }
    store.add_tick(sample_tick)

    # Resample data
    store.resample_data('BTCUSDT')

    # Get resampled data
    data_1min = store.get_resampled_data('1min', 'BTCUSDT')
    print("1-minute resampled data:")
    print(data_1min)

    store.close()
