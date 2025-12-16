# Quantitative Analytics Application

A simple but complete analytical application that ingests real-time cryptocurrency data from Binance, computes quantitative metrics, and displays them in an interactive dashboard.

## 🎯 Overview

This application demonstrates a basic quantitative analytics system with:
- Real-time data ingestion from Binance WebSocket API
- Data storage and resampling using Pandas
- Core quantitative analytics (statistics, hedge ratios, z-scores, correlations)
- Interactive Streamlit dashboard with charts and alerts
- CSV export functionality

## 🧱 Architecture

```
WebSocket Ingestion (ingestion.py)
        ↓
Pandas Data Store (storage.py)
        ↓
Analytics Engine (analytics.py)
        ↓
Streamlit Dashboard (dashboard.py)
        ↓
Alerts System (alerts.py)
```

## 📦 Installation

1. Clone or download this repository
2. Install required packages:
```bash
pip install -r requirements.txt
```

## ▶️ Running the Application

```bash
python app.py
```

This will start the Streamlit dashboard on `localhost:8501`.

## 🔬 Analytics Implemented

1. **Price Statistics**: Mean, standard deviation, returns
2. **Hedge Ratio**: Calculated using OLS regression between two assets
3. **Spread Calculation**: Difference between assets adjusted by hedge ratio
4. **Z-Score**: Rolling z-score of the spread
5. **Rolling Correlation**: Correlation between two assets over time
6. **ADF Test**: Augmented Dickey-Fuller test for stationarity (manual trigger)

## 📊 Dashboard Features

- Symbol selection (BTCUSDT, ETHUSDT)
- Timeframe selection (1s, 1min, 5min)
- Adjustable rolling window
- Interactive charts (price, spread, z-score, correlation)
- Summary statistics table
- Alert configuration and display
- CSV export for price data and analytics

## ⚠️ Limitations

- Designed for educational purposes, not production use
- Limited to 2-3 cryptocurrency pairs
- No persistent storage beyond session lifetime
- Simplified error handling
- Basic alerting system (UI only, no notifications)

## 🔮 Future Improvements

- Add more quantitative models
- Implement better data persistence
- Add more alert types
- Improve error handling and recovery
- Add more technical indicators
- Support for more cryptocurrency exchanges

## 🤖 ChatGPT Usage

This project was developed with the help of ChatGPT as a coding assistant to:
- Understand requirements and architecture
- Implement individual components
- Debug integration issues
- Optimize code for readability and performance

The implementation follows a modular approach with clear separation of concerns, making it easy to understand and extend.

## 📁 Project Structure

```
quant_app/
│
├── app.py                  # Main application entry point
├── ingestion.py            # Binance WebSocket data ingestion
├── storage.py              # Data storage and resampling
├── analytics.py            # Quantitative analytics calculations
├── alerts.py               # Alert system
├── dashboard.py            # Streamlit user interface
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🛠️ Technologies Used

- **Python**: Core programming language
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Streamlit**: Web dashboard framework
- **Plotly**: Interactive charting
- **Statsmodels**: Statistical models and tests
- **Websockets**: Real-time data streaming