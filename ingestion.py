import asyncio
import websockets
import json
import pandas as pd
from typing import List, Callable
import traceback


class BinanceDataStream:
    def __init__(self, symbols: List[str]):
        """
        Initialize Binance data stream for given symbols

        Args:
            symbols: List of trading symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
        """
        self.symbols = symbols
        self.websocket_url = "wss://stream.binance.com:9443/ws"
        self.data_callbacks = []

    def add_callback(self, callback: Callable):
        """Add a callback function to receive tick data"""
        self.data_callbacks.append(callback)

    async def connect_single_stream(self, symbol: str):
        """Connect to a single symbol stream"""
        stream_name = f"{symbol.lower()}@trade"
        url = f"{self.websocket_url}/{stream_name}"

        try:
            async with websockets.connect(url) as websocket:
                print(f"Connected to {symbol} stream")
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)

                        # Extract relevant fields
                        tick_data = {
                            'timestamp': pd.to_datetime(data['T'], unit='ms'),
                            'symbol': data['s'],
                            'price': float(data['p']),
                            'quantity': float(data['q'])
                        }

                        # Call all registered callbacks
                        for callback in self.data_callbacks:
                            try:
                                await callback(tick_data)
                            except Exception as e:
                                print(f"Error in callback: {e}")
                                traceback.print_exc()

                    except websockets.exceptions.ConnectionClosed:
                        print(
                            f"Connection closed for {symbol}, reconnecting...")
                        break
                    except Exception as e:
                        print(f"Error processing message for {symbol}: {e}")
                        traceback.print_exc()

        except Exception as e:
            print(f"Error connecting to {symbol}: {e}")
            traceback.print_exc()

    async def start_streams(self):
        """Start streams for all symbols"""
        tasks = [self.connect_single_stream(symbol) for symbol in self.symbols]
        await asyncio.gather(*tasks)

    def stop_streams(self):
        """Stop all streams (placeholder for future implementation)"""
        pass


# Example usage
if __name__ == "__main__":
    # Test the data stream
    symbols = ['BTCUSDT', 'ETHUSDT']
    stream = BinanceDataStream(symbols)

    async def print_data(data):
        print(
            f"Received: {data['symbol']} - Price: {data['price']}, Qty: {data['quantity']}")

    stream.add_callback(print_data)

    # Run the stream
    try:
        asyncio.run(stream.start_streams())
    except KeyboardInterrupt:
        print("Stopping streams...")
        stream.stop_streams()
