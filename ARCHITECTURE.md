# PricerLBSugar #11 — Architecture Document

**Product:** ICE Sugar #11 (SB) Derivatives Risk & Pricing Platform  
**Version:** 1.0  
**Classification:** Internal — Trading Desk  
**Author:** Hugo Berthelier  
**Date:** April 2026

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Repository Structure](#2-repository-structure)
3. [Module Architecture](#3-module-architecture)
4. [Data Architecture](#4-data-architecture)
5. [Financial Models](#5-financial-models)
6. [Data Flows](#6-data-flows)
7. [External Dependencies](#7-external-dependencies)
8. [Configuration & Constants](#8-configuration--constants)
9. [Risk Management Framework](#9-risk-management-framework)
10. [Performance & Scalability](#10-performance--scalability)
11. [Operational Runbook](#11-operational-runbook)
12. [Known Limitations & Roadmap](#12-known-limitations--roadmap)

---

## 1. System Overview

### 1.1 Purpose

PricerLBSugar#11 is a **single-desk derivatives pricing and risk management platform** built for ICE Sugar #11 (SB) futures and options. The system enables a commodity options trader to:

- Price and monitor a multi-account portfolio of futures and vanilla options
- Compute and aggregate all first- and second-order Greeks in real time
- Analyze the implied volatility surface across the full forward curve
- Generate delta hedging recommendations and estimate hedge cost
- Attribute live and realized P&L across risk factors (Delta, Gamma, Vega, Theta)
- Track realized performance and compute risk-adjusted return metrics

### 1.2 Instrument Specifications

| Parameter | Value |
|-----------|-------|
| Exchange | ICE Futures US (IFUS) |
| Product Code | SB (Sugar #11) |
| Underlying | Raw Cane Sugar |
| Contract Size | 112,000 lbs per lot |
| Quotation | US cents / lb |
| Tick Size | 0.01 ¢/lb |
| Tick Value | USD 11.20 per contract |
| Settlement | Physical delivery |
| Active Months | H (Mar), K (May), N (Jul), V (Oct) |
| Expiry Logic | Last business day of month preceding delivery |

### 1.3 Account Structure

| Account ID | Description |
|------------|-------------|
| 95135 | Client account 1 |
| 95136 | Client account 2 |
| 95137 | Client account 3 |

### 1.4 Covered Maturities

The system covers all active expiries from **H26 (March 2026)** through **V34 (October 2034)**, with precise first-notice dates hardcoded for each month.

---

## 2. Repository Structure

```
PricerLBSugar#11/
│
├── Cockpit.py                   # Main Streamlit dashboard — UI orchestration
├── GreeksManagement.py          # Black-76 pricing engine & Greeks computation
├── PnLComputation.py            # Realized P&L analytics & performance metrics
├── SavingsManagement.py         # Position persistence (Excel read/write)
├── API_intern.py                # Daily market data ingestion pipeline
├── vol.py                       # Implied volatility surface analysis
│
├── API_data/
│   ├── FX.xlsx                  # EUR/USD daily OHLC (auto-updated)
│   └── HistVolSB.xlsx           # SB=F daily prices + 20d realized vol
│
├── books/
│   ├── 95135/
│   │   ├── book.xlsx            # Open positions ledger
│   │   └── closed_book.xlsx     # Realized trade history
│   ├── 95136/
│   │   ├── book.xlsx
│   │   └── closed_book.xlsx
│   └── 95137/
│       ├── book.xlsx
│       └── closed_book.xlsx
│
├── vol/
│   ├── VolHbarchart.xlsx        # Implied vol smile — H (March) expiry
│   ├── VolKbarchart.xlsx        # Implied vol smile — K (May) expiry
│   ├── VolNbarchart.xlsx        # Implied vol smile — N (July) expiry
│   └── VolVbarchart.xlsx        # Implied vol smile — V (October) expiry
│
├── EmergencySavings/            # Manual position backup directory
├── ProductSpec_23.pdf           # ICE Sugar #11 contract specification
└── logo_feedalliance_couleur1.png
```

---

## 3. Module Architecture

### 3.1 High-Level Dependency Graph

```
┌──────────────────────────────────────────────────────────────┐
│                        Cockpit.py                            │
│                   (Streamlit Dashboard)                      │
│   ┌────────────┐  ┌──────────┐  ┌───────┐  ┌────────────┐  │
│   │ Main Book  │  │ Vol Tools│  │Pricer │  │ P&L Report │  │
│   └─────┬──────┘  └────┬─────┘  └───┬───┘  └──────┬─────┘  │
└─────────┼──────────────┼────────────┼──────────────┼────────┘
          │              │            │              │
   ┌──────▼──────┐  ┌────▼────┐      │       ┌──────▼──────┐
   │  Greeks     │  │ vol.py  │      │       │  PnLCompu-  │
   │ Management  │  │         │      │       │  tation.py  │
   │ .py         │  │         │      │       │             │
   └──────┬──────┘  └────┬────┘      │       └──────┬──────┘
          │              │            │              │
          └──────────────┴────────────┴──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │    SavingsManagement.py     │
                    │   (Excel I/O abstraction)   │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │       Excel Data Layer      │
                    │  books/ · vol/ · API_data/  │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │      API_intern.py          │
                    │  (Daily Scheduled Ingestion)│
                    │  yfinance: EURUSD=X, SB=F   │
                    └────────────────────────────┘
```

---

### 3.2 Cockpit.py — Dashboard Controller

**Role:** Top-level Streamlit application. Orchestrates all pages, manages session state, dispatches user inputs to the appropriate pricing/analytics modules.

**Dashboard Pages:**

| Page | Function | Key Outputs |
|------|----------|-------------|
| Main Book | Portfolio valuation, Greeks, hedging | Delta/Gamma/Vega/Theta tables, hedge recommendations, live P&L |
| Volatility Tools | IV surface & smile analytics | 2D smiles, 3D surface, term structure, skew metrics, RV |
| Pricer — Strategy | Strategy pricer (partially implemented) | Black-76 multi-leg pricing |
| Closed Positions & P&L | Realized performance analytics | Equity curve, Sharpe, Max Drawdown, win rate |

**Key Constants Declared Here:**

```python
CONTRACT_MULTIPLIER = 112_000          # lbs per contract
DEFAULT_VOL          = { "H27": 0.20,  # Fallback IV by expiry
                         "K26": 0.20, ... }
EXPIRY_DATES         = { 2026: {3: 13, 5: 14, 7: 14, 10: 14}, ... }
accounts             = { "95135": {...}, "95136": {...}, "95137": {...} }
```

---

### 3.3 GreeksManagement.py — Pricing Engine

**Role:** Core quantitative library. Implements the Black-76 model for European futures options. Computes all eight Greeks, aggregates by expiry, and provides hedging advisory output.

#### 3.3.1 Pricing Model: Black-76

For a European option on a futures contract:

```
d₁ = [ ln(F/K) + (σ²/2)·T ] / (σ·√T)
d₂ = d₁ - σ·√T

Call = exp(-r·T) · [ F·N(d₁) - K·N(d₂) ]
Put  = exp(-r·T) · [ K·N(-d₂) - F·N(-d₁) ]
```

Where:
- `F` = futures price (spot quotation, ¢/lb)
- `K` = strike price
- `σ` = implied volatility (decimal, annualized)
- `T` = time to expiry (ACT/252 years)
- `r` = risk-free rate (2%, continuous)
- `N(·)` = standard normal CDF

#### 3.3.2 Greeks Catalog

| Greek | Symbol | Formula | Unit | Use |
|-------|--------|---------|------|-----|
| Delta | Δ | N(d₁) / N(d₁)-1 | ratio | Directional hedge sizing |
| Gamma | Γ | n(d₁) / (F·σ·√T) | 1/price | Convexity, re-hedge frequency |
| Vega | ν | F·n(d₁)·√T | cts/1% IV | Vol exposure by expiry |
| Theta | Θ | -F·n(d₁)·σ/(2√T)/252 | USD/day | Daily time decay |
| Rho | ρ | -T·V | USD/1%r | Interest rate sensitivity |
| Vanna | Vα | √T·n(d₁)·[1 - d₁/(σ√T)] | mixed | Delta sensitivity to vol |
| Volga | Vο | F·√T·n(d₁)·d₁·d₂/σ | mixed | Smile/convexity exposure |
| Charm | Χ | -n(d₁)/(2T) | ratio/day | Delta decay toward expiry |

#### 3.3.3 Public API

```python
# Single-position Greeks (pure functions, O(1))
single_delta(F, K, T, sigma, r, option_type)
single_gamma(F, K, T, sigma, r)
single_vega(F, K, T, sigma, r)
single_theta(F, K, T, sigma, r, option_type)
single_rho(F, K, T, sigma, r, option_type, qty, mult)
single_vanna(F, K, T, sigma, r)
single_volga(F, K, T, sigma, r)
single_charm(F, K, T, sigma, r, option_type)

# Portfolio aggregation by expiry
portfolio_delta_by_expiry(df)    # → {expiry: Δ_total}
portfolio_gamma_by_expiry(df)
portfolio_vega_by_expiry(df)
portfolio_theta_by_expiry(df)

# Hedging advisory
delta_hedge_action_by_expiry(df)     # → {expiry: ("Buy"|"Sell"|"Hold", qty)}
hedge_cash_cost_by_expiry(df, prices)# → {expiry: USD_cost}

# Visualization (Plotly)
plot_delta_vs_future_subplots(df, ±10% range)
plot_gamma_vs_future_subplots(df, ±10% range)
plot_vega_vs_future_subplots(df, ±10% range)
plot_theta_vs_future_subplots(df, ±10% range)

# P&L engine
compute_live_pnl(df, prices, vols)      # Mark-to-market
compute_pnl_explain(df, old, new)       # Attribution: Δ/Γ/ν/Θ
```

---

### 3.4 vol.py — Volatility Surface Engine

**Role:** Load, clean, interpolate, and visualize the implied volatility surface across all active expiries. Compute smile metrics (Risk Reversal, Butterfly, Put Skew) and realized volatility.

#### 3.4.1 Pipeline

```
VolH/K/N/V barchart.xlsx
        │
        ▼
load_raw_vol_data()         # pd.read_excel per expiry
        │
        ▼
clean_vol_data()            # "27.5%" → 0.275 · "117.25s" → 117.25
        │
        ▼
add_smile_metrics_black76() # IV_Mid, Delta_Signed, Delta_Abs
        │
        ├──────────────────────────────────────────────────┐
        ▼                                                  ▼
build_vol_surface_matrix()              compute_atm_term_structure()
  K_grid: linspace(K_min, K_max, 60)     IV at F by expiry
  IV:     2D array (T × K)
  Interp: linear/bilinear, no extrap
```

#### 3.4.2 Smile Metrics

```
Risk Reversal (RR_Δ)  =  IV_Call(+Δ) - IV_Put(-Δ)      [skew direction]
Butterfly (BF_Δ)      =  0.5·(IV_Call + IV_Put) - IV_ATM [smile curvature]
Put Skew              =  IV_Put(Δ) - IV_ATM               [downside premium]

Slope_Left   = (IV_ATM - IV_Put) / Δ
Slope_Right  = (IV_Call - IV_ATM) / Δ
Curvature    =  IV_Call + IV_Put - 2·IV_ATM
Vol Misprice = IV(K) - IV_ATM                             [heatmap]
```

Computed at **10Δ** and **25Δ** for each active expiry.

#### 3.4.3 Visualization Functions

| Function | Output | Mode |
|----------|--------|------|
| `plot_smiles_panel()` | 2D smile per expiry | Strike / Signed Δ / Abs Δ |
| `plot_vol_surface()` | 3D IV surface | Plotly 3D mesh |
| `plot_atm_term_structure()` | ATM IV vs T | Line chart |
| `plot_skew_bars()` | RR, BF, PutSkew bars | Bar chart (10Δ & 25Δ) |
| `plot_shape_lines()` | Slope & curvature | Line chart |
| `plot_vol_mispricing_heatmap()` | IV − IV_ATM | Heatmap |

---

### 3.5 PnLComputation.py — Performance Analytics

**Role:** Compute, aggregate, and analyze realized P&L from closed trades. Produce risk-adjusted performance metrics.

#### 3.5.1 Data Model (closed_book.xlsx)

| Column | Type | Description |
|--------|------|-------------|
| trade_id | str | Unique trade identifier |
| date | date | Trade close date |
| open_date | date | Trade entry date |
| underlying | str | "SB" |
| type | str | "fut", "call", "put" |
| expiry | str | "H26", "K26", … |
| quantity | float | Signed lot size |
| strike | float | Strike (options only) |
| price/premium | float | Entry price (¢/lb) |
| end_price | float | Exit price (¢/lb) |
| cost | float | Commissions & fees |

#### 3.5.2 P&L Formula

```
PnL (trade) = (end_price − entry_price) × quantity × 112,000
              − cost

PnL (portfolio) = Σ PnL (trade)
```

#### 3.5.3 Aggregation Methods

| Dimension | Function | Output |
|-----------|----------|--------|
| Per trade | `compute_line_pnl()` | PnL, holding_days, data_ok |
| By expiry | `compute_pnl_by_expiry()` | PnL sum, trade count |
| By month | `compute_pnl_by_month()` | Monthly P&L |
| By year | `compute_pnl_by_year()` | Annual P&L |
| Daily cumulative | `build_daily_pnl_series()` | Equity curve |
| YTD cumulative | `build_daily_pnl_series_by_year()` | Per-year equity curve |

#### 3.5.4 Risk Metrics

```python
Sharpe Ratio     = √252 · mean(excess_returns) / std(returns)
Max Drawdown     = min( (equity_t / peak_t) − 1 )
Win Rate         = count(PnL > 0) / total_trades
```

---

### 3.6 SavingsManagement.py — Persistence Layer

**Role:** Thin abstraction over Excel-based position storage. Isolates all file I/O from business logic.

```python
load_open_positions(account_id: str)  → pd.DataFrame
save_open_positions(account_id: str, df: pd.DataFrame) → None
```

**Storage Paths:**
```
books/{account_id}/book.xlsx         # Open positions
books/{account_id}/closed_book.xlsx  # Closed trades
```

---

### 3.7 API_intern.py — Market Data Ingestion

**Role:** Scheduled data pipeline that downloads and persists daily market data from Yahoo Finance.

**Schedule:** Windows Task Scheduler — business days, market open

| Step | Ticker | Fields | Output |
|------|--------|--------|--------|
| 1 | EURUSD=X | OHLC, last 14d | API_data/FX.xlsx |
| 2 | (pause 3s) | — | rate-limiting |
| 3 | SB=F | OHLC + rolling vol, last 365d | API_data/HistVolSB.xlsx |

**Computed fields on SB=F:**
```python
rets         = close.pct_change()
vol_CtoC_20d = rets.rolling(20).std() * sqrt(252)   # annualized
```

---

## 4. Data Architecture

### 4.1 Data Sources

| Source | Type | Data | Update | Format |
|--------|------|------|--------|--------|
| Yahoo Finance | REST API (yfinance) | EUR/USD, SB=F prices | Daily (auto) | In-memory → Excel |
| Barchart / CMDty Views | Manual export | Implied vol smiles | Ad-hoc (manual) | Excel |
| Trader input | Manual | Open & closed positions | Real-time | Excel |

### 4.2 Data Layer Layout

```
API_data/
  FX.xlsx              EUR/USD daily OHLC — used for USD→EUR P&L conversion
  HistVolSB.xlsx       SB=F close prices, log-returns, 20d realized vol

books/
  {acct}/book.xlsx     Open positions — live risk book
  {acct}/closed_book.xlsx  Closed trades — realized P&L ledger

vol/
  VolH/K/N/Vbarchart.xlsx  Implied vol smile per expiry (Barchart format)
    Columns: Δ_Call · IV_Call · Strike · IV_Put · Δ_Put
```

### 4.3 Excel Schema — Open Positions (book.xlsx)

| Column | Type | Description |
|--------|------|-------------|
| trade_id | str | Unique position ID |
| date | date | Entry date |
| underlying | str | "SB" |
| type | str | "fut" / "call" / "put" |
| expiry | str | "H26", "K26", … |
| quantity | float | Signed lots (+long, −short) |
| strike | float | Strike in ¢/lb (options) |
| price/premium | float | Entry price |
| implied_vol | float | IV at entry (decimal) |

---

## 5. Financial Models

### 5.1 Black-76 Model

Used for all options pricing and Greeks computation.

**Assumptions:**
- Log-normal distribution of futures prices
- Constant implied volatility per option (no smile dynamics in pricing)
- Continuous risk-free rate, no dividends
- No transaction costs, no jumps

**Day Count Convention:**
- Time to maturity: ACT/365
- Theta & realized vol annualization: ACT/252

**Interest Rate:** `r = 2%` (hardcoded, represents approximate cost of carry)

**Normal Distribution Implementation:**
```python
N(x)  = 0.5 · [1 + erf(x / √2)]    # CDF  — scipy-free, uses math.erf
n(x)  = exp(-0.5·x²) / √(2π)        # PDF
```

### 5.2 Volatility Surface Construction

**Interpolation:**
- Within expiry (strike axis): piecewise linear interpolation
- Across expiries (time axis): bilinear interpolation
- No extrapolation beyond observed data bounds (returns NaN)
- No arbitrage enforcement (not implemented)

**Input Grid:** 60 uniformly spaced strike points between observed min/max per expiry.

### 5.3 P&L Attribution Model

Mark-to-market P&L is decomposed using the Taylor expansion of the option pricing function:

```
dP = Δ·dF + ½·Γ·(dF)² + ν·dσ + Θ·dt + residual
```

Where the residual captures higher-order terms, model error, and smile dynamics.

### 5.4 Realized Volatility

```
r_t   = ln(Close_t / Close_{t-1})          # log-return
σ_RV  = std(r_t, window=20) × √252          # 20-day close-to-close, annualized
```

Used as a benchmark against implied volatility to assess vol richness/cheapness.

---

## 6. Data Flows

### 6.1 Portfolio Valuation & Greeks

```
User Input
  │  Account ID, Valuation Date, Futures Prices {expiry: F}, IVs
  ▼
SavingsManagement.load_open_positions()
  │  book.xlsx → DataFrame
  ▼
GreeksManagement.add_ttm_column()
  │  Expiry string → T (years) via EXPIRY_DATES lookup
  ▼
GreeksManagement.build_greeks_dataframe()
  │  Per position: Δ, Γ, ν, Θ, ρ, Vα, Vο, Χ  (Black-76)
  ▼
portfolio_{greek}_by_expiry()
  │  Aggregate by maturity bucket
  ▼
delta_hedge_action_by_expiry()
  │  → {expiry: ("Buy"|"Sell"|"Hold", qty, USD_cost)}
  ▼
compute_live_pnl() + compute_pnl_explain()
  │  Mark-to-market → Attribution: Δ/Γ/ν/Θ/residual
  ▼
Cockpit.py (Streamlit rendering)
```

### 6.2 Volatility Surface Analysis

```
User Input
  │  Expiry selection, View mode (Strike/SignedΔ/AbsΔ), Shape delta
  ▼
vol.load_raw_vol_data()  ←  VolH/K/N/V barchart.xlsx
  ▼
vol.clean_vol_data()
  │  Parse %, strings → floats; map columns
  ▼
vol.add_smile_metrics_black76()
  │  IV_Mid, Delta_Signed, Delta_Abs
  ▼
┌──────────────────────────────────────────────────────┐
│  build_vol_surface_matrix()    compute_atm_ts()      │
│  compute_skew_metrics()        plot functions        │
└──────────────────────────────────────────────────────┘
  ▼
Historical Volatility
  │  API_data/HistVolSB.xlsx → vol_CtoC_20d + returns histogram
  ▼
Cockpit.py (Plotly visualizations)
```

### 6.3 Realized P&L Analytics

```
User Input
  │  Account ID
  ▼
PnLComputation.load_closed_positions()  ←  closed_book.xlsx
  ▼
compute_line_pnl()
  │  (end_price − entry_price) × qty × 112,000 − cost
  ▼
Aggregation layer
  │  By trade · by expiry · by month · by year · daily
  ▼
build_daily_pnl_series()  →  Equity curve
compute_sharpe(), compute_max_drawdown()
  ▼
FX Conversion
  │  API_data/FX.xlsx  →  latest EUR/USD  →  P&L (EUR)
  ▼
Cockpit.py (Charts + metrics)
```

### 6.4 Daily Market Data Update

```
Windows Task Scheduler (business days, 08:00)
  ▼
API_intern.py
  ├── yfinance.download("EURUSD=X", period="14d")
  │     → API_data/FX.xlsx
  │
  ├── sleep(3s)
  │
  └── yfinance.download("SB=F", period="1y")
        compute returns + 20d realized vol
        → API_data/HistVolSB.xlsx
```

---

## 7. External Dependencies

### 7.1 Python Libraries

| Library | Purpose |
|---------|---------|
| `streamlit` | Web framework — dashboard UI |
| `pandas` | DataFrame operations, Excel I/O |
| `numpy` | Numerical arrays, vectorized math |
| `plotly` | Interactive visualization (web-based) |
| `matplotlib` | Static plots (fallback) |
| `yfinance` | Market data download (Yahoo Finance) |
| `openpyxl` | Excel read/write (.xlsx) |
| `math` | `erf()`, `sqrt()` for normal distribution |
| `pathlib` | Cross-platform file path handling |
| `datetime` | Date arithmetic, TTM calculation |

### 7.2 External Data Sources

| Source | Ticker / URL | Data | Auth | Latency |
|--------|-------------|------|------|---------|
| Yahoo Finance | `EURUSD=X` | EUR/USD daily | None (public) | ~15 min |
| Yahoo Finance | `SB=F` | Sugar #11 front month daily | None (public) | ~15 min |
| Barchart.com | CMDty Views export | Implied vol smiles | Manual login | Manual |

---

## 8. Configuration & Constants

### 8.1 Model Parameters

| Parameter | Value | Location | Description |
|-----------|-------|----------|-------------|
| `CONTRACT_MULTIPLIER` | 112,000 | Cockpit.py | lbs per lot |
| `r` | 0.02 | GreeksManagement.py | Risk-free rate (continuous) |
| `storage_cost` | 0.02 | GreeksManagement.py | Commodity carrying cost |
| `day_count_ttm` | 365 | GreeksManagement.py | ACT/365 for TTM |
| `day_count_theta` | 252 | GreeksManagement.py | ACT/252 for Theta |
| `n_strikes_grid` | 60 | vol.py | Strike interpolation grid size |

### 8.2 Calendar — Expiry Dates

First-notice dates by year and delivery month:

```python
FUTURES_MONTH_MAP = {"H": 3, "K": 5, "N": 7, "V": 10}

EXPIRY_DATES = {
    2026: {3: 13, 5: 14, 7: 14, 10: 14},
    2027: {3: 12, 5: 14, 7: 14, 10: 14},
    2028: {3: 14, 5: 14, 7: 14, 10: 14},
    # ... through 2034
}
```

### 8.3 Default Volatilities

Fallback IV used when live smile data is unavailable:

```python
DEFAULT_VOL = {
    "H27": 0.20,
    "K26": 0.20,
    "N26": 0.20,
    "V26": 0.20,
    # ...
}
```

### 8.4 File Paths

| Path | OS | Used By |
|------|----|---------|
| `/Users/hugoberthelier/Desktop/PricerLBSugar#11/books` | macOS | SavingsManagement.py |
| `C:/PricerLb/PricerLBSugar#11/books` | Windows | SavingsManagement.py |
| `C:/PricerLb/PricerLBSugar#11/vol/` | Windows | vol.py |

> **Note:** Dual-path support for macOS and Windows present. Paths are hardcoded and must be updated manually on new deployments.

---

## 9. Risk Management Framework

### 9.1 Greeks-Based Risk Dashboard

The system implements a full Greeks ladder aggregated by maturity bucket:

```
Portfolio Risk (by expiry)
┌──────┬──────────┬──────────┬─────────┬──────────────┬────────┐
│Expiry│  Delta   │  Gamma   │  Vega   │  Theta($/d)  │ Action │
├──────┼──────────┼──────────┼─────────┼──────────────┼────────┤
│ H26  │  −14.3   │  +0.023  │  +182   │  −1,240      │ Buy 14 │
│ K26  │  +6.1    │  −0.011  │  −78    │  +560        │ Sell 6 │
│ N26  │  +0.0    │  +0.000  │  +0     │  +0          │ Hold   │
└──────┴──────────┴──────────┴─────────┴──────────────┴────────┘
```

### 9.2 Delta Hedging Advisory

For each expiry, the system computes:

```
hedge_qty    = round( |Δ_portfolio| )
action       = "Buy"  if Δ < −threshold
             = "Sell" if Δ > +threshold
             = "Hold" otherwise
hedge_cost   = hedge_qty × F × 112,000   (USD notional)
```

### 9.3 Sensitivity Analysis

Greeks vs. futures price across a ±10% price range are plotted per expiry, enabling scenario analysis:

- Delta profile (linearity check, strike proximity)
- Gamma profile (convexity peak around ATM)
- Vega profile (long/short vol positioning)
- Theta profile (daily P&L under price moves)

### 9.4 P&L Attribution

Live P&L is decomposed into:

```
dP = Δ·dF + ½Γ·(dF)² + ν·dσ + Θ·dt + ε
     [dir.]  [convex]  [vol]  [time]  [residual]
```

This allows instant identification of the source of any P&L surprise.

### 9.5 Performance KPIs (Realized Book)

| Metric | Formula |
|--------|---------|
| Sharpe Ratio | √252 × E[r − r_f] / σ_r |
| Max Drawdown | min((equity_t / peak_t) − 1) |
| Win Rate | count(PnL_trade > 0) / n_trades |
| Annual P&L | Σ daily P&L per calendar year |

### 9.6 Not Yet Implemented

The following risk controls are identified as future priorities:

- Value-at-Risk (VaR 95/99%) and Expected Shortfall (CVaR)
- Stress testing (parallel/tilt shifts of vol surface, price gaps)
- Basis risk (physical vs. futures basis)
- Jump risk modeling
- Hard position limits enforcement
- Correlation / cross-commodity risk

---

## 10. Performance & Scalability

### 10.1 Computational Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Single Greek | O(1) | Closed-form Black-76 |
| Portfolio Greeks | O(n) | n = number of open positions |
| Vol surface build | O(m × k) | m expiries, k strike points |
| P&L aggregation | O(n) | n = number of closed trades |
| Delta hedging | O(m log m) | Sort by expiry |

**Expected performance:** Sub-second computation for portfolios up to ~10,000 positions.

### 10.2 Scalability Limitations

| Constraint | Current Limit | Bottleneck |
|------------|--------------|------------|
| Positions | ~500–1,000 | Excel read/write latency |
| Expiries | 8 active | Hardcoded EXPIRY_DATES |
| Users | 1 (single-user) | Local Streamlit, no auth |
| Data refresh | Manual / daily | No real-time feed |
| Vol data | 4 expiries | 4 Excel files |

---

## 11. Operational Runbook

### 11.1 Daily Workflow

```
Pre-Market (automated):
  API_intern.py runs via Task Scheduler
    → FX.xlsx updated (EUR/USD)
    → HistVolSB.xlsx updated (SB=F prices + RV)

Morning (manual):
  1. Open Terminal / Command Prompt
     $ cd PricerLBSugar#11
     $ streamlit run Cockpit.py

  2. Select account (95135 / 95136 / 95137)

  3. Set valuation date (defaults to today)

  4. Enter current futures prices by expiry
     (H26: 15.50, K26: 15.30, ...)

  5. Review Main Book:
     - Check Greeks ladder
     - Review delta hedging recommendations
     - Monitor live P&L attribution

  6. Upload vol smile files (if updated from Barchart):
     vol/VolH/K/N/Vbarchart.xlsx

  7. Review Volatility Tools:
     - Check ATM term structure
     - Analyze skew (RR, BF)
     - Compare IV vs 20d RV

End of Day:
  8. Close trades → update closed_book.xlsx
  9. Save positions → Cockpit "Save" action
  10. Archive books/{acct}/ to EmergencySavings/
```

### 11.2 Maintenance Tasks

| Frequency | Task |
|-----------|------|
| Weekly | Verify API_intern.py logs for failures |
| Monthly | Reconcile closed_book.xlsx with broker statements |
| Quarterly | Add new year's EXPIRY_DATES to GreeksManagement.py |
| Quarterly | Recalibrate DEFAULT_VOL dictionary |
| Annually | Review model assumptions (r, storage_cost, day_count) |
| Ad-hoc | Update file paths on new machine/OS |

### 11.3 Running the Application

```bash
# Install dependencies (first time)
pip install streamlit pandas numpy plotly matplotlib yfinance openpyxl

# Launch dashboard
streamlit run Cockpit.py

# Run data pipeline manually
python API_intern.py
```

---

## 12. Known Limitations & Roadmap

### 12.1 Current Limitations

| Category | Issue | Severity |
|----------|-------|----------|
| Infrastructure | Hardcoded absolute file paths | High |
| Infrastructure | Excel-only persistence (no database) | High |
| Infrastructure | Single-user, local Streamlit only | Medium |
| Model | Constant volatility (no stochastic vol) | Medium |
| Model | No arbitrage-free vol surface | Medium |
| Model | No VaR / CVaR implementation | Medium |
| Operations | No audit trail for trade entry | High |
| Operations | No real-time data feed | Medium |
| Operations | No unit tests | Medium |
| Operations | No input validation on Excel | Medium |
| Compliance | No trade confirmation workflow | High |
| Compliance | No regulatory reporting | High |

### 12.2 Technical Debt

- File paths must be parameterized via environment variables or config file
- `DEFAULT_VOL` dictionary must be externalized to a config
- Day count conventions are inconsistent across modules (365 vs 252)
- Vol interpolation does not enforce no-arbitrage (calendar spread, butterfly)
- `API_intern.py` uses Windows Task Scheduler; not portable to macOS/Linux

### 12.3 Priority Roadmap

**Short-term (v1.1):**
- [ ] Externalize config to `config.yaml` (paths, constants, accounts)
- [ ] Add input validation layer for Excel position files
- [ ] Implement basic logging throughout all modules
- [ ] Add VaR (historical simulation) to P&L page

**Medium-term (v1.2):**
- [ ] Replace Excel data layer with SQLite or PostgreSQL
- [ ] Add real-time futures price feed (Interactive Brokers API or Refinitiv)
- [ ] Implement arbitrage-free vol interpolation (SVI / SABR)
- [ ] Stress testing module (parallel vol shifts, price shock scenarios)

**Long-term (v2.0):**
- [ ] Stochastic volatility model (Heston or SABR)
- [ ] Monte Carlo scenario engine
- [ ] Multi-user support with RBAC and audit logging
- [ ] FIX protocol integration for automated trade capture
- [ ] Compliance reporting module

---

*PricerLBSugar#11 — Architecture Document — v1.0 — April 2026*  
*Internal use only — Trading Desk*
