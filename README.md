# PricerLB — ICE Sugar #11 (SB) Options Pricing & Risk Management Dashboard

A professional-grade Streamlit dashboard for managing ICE Sugar #11 (SB) futures and options positions across multiple client accounts. Built around the **Black-76 model**, it provides full Greeks computation, P&L attribution, volatility surface analysis, and a multi-leg strategy pricer — with an automated daily market data pipeline.

> **Disclaimer:** All datasets included in this repository (positions, trades, account data) are **fictional and fully anonymized**. They do not represent any real trading activity, real accounts, or any real financial institution. They are provided solely for demonstration purposes.

---

## Features

### Open Positions & Greeks Dashboard
- Real-time Greeks computation: **Delta, Gamma, Vega, Theta, Rho, Vanna, Volga, Charm**
- Portfolio aggregation by expiry and instrument type
- Delta hedge advisor with optimal sizing and estimated notional cost
- Live P&L tracking with full attribution (Delta PnL, Gamma PnL, Vega PnL, Theta PnL)
- Multi-account support: accounts **95135**, **95136**, **95137**
- Market inputs for 4 active expiries: H (Mar), K (May), N (Jul), V (Oct)

### P&L Analytics (Closed Positions)
- Realized P&L breakdown by trade, month, year, and expiry
- Daily equity curve and cumulative performance
- EUR/USD conversion via live FX data
- Key statistics: **Sharpe ratio, max drawdown, win rate**, trade count

### Volatility Tools
- Implied volatility smile visualization — by strike, by signed delta, or by absolute delta
- ATM vol term structure across expiries
- Skew metrics: **25Δ / 10Δ Risk Reversal (RR), Butterfly (BF), Put Skew**
- Smile shape analysis: slopes and curvature
- Interactive **3D volatility surface** (Plotly)
- Vol mispricing heatmap vs ATM baseline
- Historical realized volatility (20-day close-to-close) vs implied vol comparison

### Strategy Pricer
- Multi-leg strategy builder interface
- Black-76 pricing for custom option combinations
- Per-leg Greeks and cost breakdown

### Automated Market Data Pipeline
- Daily ingestion of **EUR/USD** (EURUSD=X) and **Sugar #11** (SB=F) prices via Yahoo Finance
- Automatic computation of 20-day annualized realized volatility
- Scheduled via Windows Task Scheduler (business days)

---

## Architecture

```
PricerLBSugar#11/
├── Cockpit.py                   # Main Streamlit app (4-page dashboard)
├── GreeksManagement.py          # Black-76 Greeks engine
├── PnLComputation.py            # Realized P&L analytics
├── vol.py                       # Volatility surface & smile tools
├── SavingsManagement.py         # Excel I/O for position data
├── API_intern.py                # Daily market data ingestion pipeline
│
├── API_data/
│   ├── FX.xlsx                  # EUR/USD daily OHLC (auto-updated)
│   └── HistVolSB.xlsx           # SB=F daily prices + 20d realized vol
│
├── books/                       # Fictional position data (per account)
│   ├── 95135/
│   │   ├── book.xlsx            # Open positions
│   │   └── closed_book.xlsx     # Closed/historical trades
│   ├── 95136/
│   │   ├── book.xlsx
│   │   └── closed_book.xlsx
│   └── 95137/
│       ├── book.xlsx
│       └── closed_book.xlsx
│
├── vol/                         # Implied volatility data (by expiry)
│   ├── VolHbarchart.xlsx        # March expiry (H)
│   ├── VolKbarchart.xlsx        # May expiry (K)
│   ├── VolNbarchart.xlsx        # July expiry (N)
│   └── VolVbarchart.xlsx        # October expiry (V)
│
└── EmergencySavings/            # Manual position backup directory
```

---

## Data Formats

**Open positions** (`book.xlsx`) — columns: `trade_id`, `date`, `underlying`, `type`, `expiry`, `quantity`, `strike`, `price/premium`, `implied_vol`

Instrument types: `fut` (futures), `call`, `put`

**Closed positions** (`closed_book.xlsx`) — same schema with additional `open_date`, `end_price`, and `cost` columns.

**Implied vol files** (`vol/*.xlsx`) — pivot table by strike: `Delta_Call`, `ImplV_Call`, `Strike`, `ImplV_Put`, `Delta_Put`

**Market data** (`API_data/*.xlsx`) — `FX.xlsx`: EUR/USD OHLC · `HistVolSB.xlsx`: SB=F close prices, log-returns, 20d realized vol

---

## Contract Specifications

| Parameter | Value |
|-----------|-------|
| Exchange | ICE Futures US (IFUS) |
| Underlying | Raw Cane Sugar #11 (SB) |
| Pricing model | Black-76 |
| Contract size | 112,000 lbs per lot |
| Quotation | US cents / lb |
| Tick size | 0.01 ¢/lb |
| Tick value | USD 11.20 per contract |
| Settlement | Physical delivery |
| Risk-free rate (default) | 2% |
| Day count (TTM) | ACT/365 |
| Day count (Theta / RV) | ACT/252 |

Active expiry months: **H** = Mar · **K** = May · **N** = Jul · **V** = Oct  
Termination: last business day of the month preceding delivery

---

## Getting Started

### Prerequisites

```bash
pip install streamlit pandas numpy plotly matplotlib yfinance openpyxl
```

### Run the dashboard

```bash
streamlit run Cockpit.py
```

The app will open at `http://localhost:8501` in your browser.

### Run the data pipeline manually

```bash
python API_intern.py
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI / App framework | [Streamlit](https://streamlit.io/) |
| Numerical computing | NumPy, pandas |
| Visualization | Plotly, Matplotlib |
| Options model | Black-76 |
| Market data | yfinance (Yahoo Finance) |
| Data storage | Excel (.xlsx) via openpyxl |
| Language | Python 3.10+ |

---

## Disclaimer

This project is an academic and personal portfolio project. The datasets included are **entirely fictional and anonymized** — no real client, account, or trade data is present in this repository. The tool is designed for educational and demonstration purposes.

---

## Author

Hugo Berthelier — EDHEC Business School x Centrale Lille  
[hugo.berthelier@edhec.com](mailto:hugo.berthelier@edhec.com)
