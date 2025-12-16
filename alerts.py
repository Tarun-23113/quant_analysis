import pandas as pd
from typing import List, Dict, Callable
import threading


class AlertSystem:
    def __init__(self):
        """Initialize alert system"""
        self.alerts = []  # List of active alerts
        self.alert_history = []  # History of triggered alerts
        self.lock = threading.Lock()

    def add_alert(self, name: str, condition_func: Callable, symbol: str = None):
        """
        Add a new alert

        Args:
            name: Name of the alert
            condition_func: Function that takes data and returns True if alert should trigger
            symbol: Symbol this alert applies to (optional)
        """
        alert = {
            'name': name,
            'condition_func': condition_func,
            'symbol': symbol,
            'active': True
        }

        with self.lock:
            self.alerts.append(alert)

    def remove_alert(self, name: str):
        """
        Remove an alert by name

        Args:
            name: Name of the alert to remove
        """
        with self.lock:
            self.alerts = [
                alert for alert in self.alerts if alert['name'] != name]

    def check_alerts(self, data: pd.DataFrame, symbol: str = None) -> List[Dict]:
        """
        Check all active alerts against provided data

        Args:
            data: DataFrame with current data
            symbol: Symbol to check alerts for (optional)

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []

        with self.lock:
            for alert in self.alerts:
                # Skip if alert is not active
                if not alert['active']:
                    continue

                # Skip if symbol doesn't match (when specified)
                if alert['symbol'] and symbol and alert['symbol'] != symbol:
                    continue

                try:
                    # Check if alert condition is met
                    if alert['condition_func'](data):
                        triggered_alert = {
                            'name': alert['name'],
                            'symbol': symbol or alert['symbol'],
                            'timestamp': pd.Timestamp.now()
                        }
                        triggered_alerts.append(triggered_alert)

                        # Add to history
                        self.alert_history.append(triggered_alert)

                except Exception as e:
                    print(f"Error checking alert {alert['name']}: {e}")

        return triggered_alerts

    def get_alert_history(self) -> List[Dict]:
        """
        Get history of all triggered alerts

        Returns:
            List of triggered alerts
        """
        with self.lock:
            return self.alert_history.copy()

    def activate_alert(self, name: str):
        """Activate an alert"""
        with self.lock:
            for alert in self.alerts:
                if alert['name'] == name:
                    alert['active'] = True
                    break

    def deactivate_alert(self, name: str):
        """Deactivate an alert"""
        with self.lock:
            for alert in self.alerts:
                if alert['name'] == name:
                    alert['active'] = False
                    break

    def get_active_alerts(self) -> List[Dict]:
        """Get list of active alerts"""
        with self.lock:
            return [alert for alert in self.alerts if alert['active']]


# Example usage
if __name__ == "__main__":
    # Test the alert system
    alert_system = AlertSystem()

    # Define a sample alert condition (z-score > 2)
    def zscore_alert(data):
        if 'zscore' not in data.columns:
            return False
        latest_zscore = data['zscore'].iloc[-1] if len(data) > 0 else 0
        return abs(latest_zscore) > 2

    # Add alert
    alert_system.add_alert("Z-Score Alert", zscore_alert, "BTCUSDT")

    # Create sample data that would trigger the alert
    sample_data = pd.DataFrame({
        'zscore': [0.5, 1.2, 2.5, 1.8]  # Last value > 2
    })

    # Check alerts
    triggered = alert_system.check_alerts(sample_data, "BTCUSDT")
    print("Triggered alerts:", triggered)

    # Check history
    history = alert_system.get_alert_history()
    print("Alert history:", history)
