# System Architecture — PricerLB Sugar #11
**Version:** 1.0 | **Asset Class:** Agricultural Commodities — ICE Sugar #11 (SB) | **Model:** Black-76

---

## 1. Executive Overview

PricerLBSugar#11 is a single-dealer risk management and pricing platform for ICE Sugar #11 (SB) options and futures, covering three managed client accounts. It provides real-time Greeks aggregation, P&L attribution, implied volatility surface construction, and a multi-leg strategy pricer — all within a unified, session-aware dashboard.

The system is organized around a **thin orchestration layer** (`Cockpit.py`) that delegates all quantitative logic to four specialized modules. Market data flows from **two sources**: implied volatility smiles are ingested from **Barchart Cmdty** manual exports, while daily futures prices and EUR/USD rates are fetched automatically from **Yahoo Finance** via a scheduled `API_intern.py` pipeline. Data persistence relies on Excel workbooks, enabling lightweight deployment with no database infrastructure.

---

## 2. High-Level System Architecture

```mermaid
graph TB
    User(["Trader / Risk Manager\n(Browser — localhost:8501)"])

    subgraph App["PricerLBSugar#11 Application Layer  ·  Streamlit Runtime"]
        direction TB
        Cockpit["Cockpit.py\nOrchestration & Session State\nPage routing · Market input management"]

        subgraph Pages["Presentation Layer — 4 Modules"]
            P1["Main Book\nOpen Positions & Greeks"]
            P2["Closed Positions\nP&L Analytics & Reporting"]
            P3["Volatility Tools\nSurface & Smile Analysis"]
            P4["Strategy Pricer\nMulti-leg Builder"]
        end

        subgraph Engine["Quantitative Engine"]
            GM["GreeksManagement.py\nBlack-76 Pricing Engine\n──────────────────────\nFull Greeks · PnL Attribution\nDelta Hedge Advisor\nPortfolio Aggregation"]
            PL["PnLComputation.py\nRisk & Performance Analytics\n──────────────────────\nEquity Curve · Sharpe Ratio\nMax Drawdown · Win Rate\nYTD / Inception Attribution\nEUR/USD FX Conversion"]
            VOL["vol.py\nVolatility Surface Engine\n──────────────────────\nSmile Construction · Term Structure\nRisk Reversal · Butterfly\n3D Surface · Mispricing Map\n20d Realized Vol vs IV"]
            SM["SavingsManagement.py\nData Access Layer\n──────────────────────\nPositions I/O\nExcel Read / Write"]
            API["API_intern.py\nMarket Data Pipeline\n──────────────────────\nyfinance: EURUSD=X · SB=F\n20d Realized Vol computation\nWindows Task Scheduler"]
        end
    end

    subgraph DataLayer["Persistence Layer — Excel Workbooks"]
        direction LR
        subgraph Books["books/  ·  Position Store"]
            B1["95135/\nbook.xlsx · closed_book.xlsx"]
            B2["95136/\nbook.xlsx · closed_book.xlsx"]
            B3["95137/\nbook.xlsx · closed_book.xlsx"]
        end
        subgraph VolStore["vol/  ·  Implied Volatility Store\n(Barchart Cmdty — manual export)"]
            V1["VolHbarchart.xlsx  — Mar (H)"]
            V2["VolKbarchart.xlsx  — May (K)"]
            V3["VolNbarchart.xlsx  — Jul (N)"]
            V4["VolVbarchart.xlsx  — Oct (V)"]
        end
        subgraph APIData["API_data/  ·  Market Data Store\n(Yahoo Finance — auto-updated)"]
            A1["FX.xlsx\nEUR/USD daily OHLC"]
            A2["HistVolSB.xlsx\nSB=F daily prices\n+ 20d realized vol"]
        end
    end

    User -->|"HTTP / WebSocket"| Cockpit
    Cockpit --> P1 & P2 & P3 & P4

    P1 --> GM & SM
    P2 --> PL & SM
    P3 --> VOL
    P4 --> GM

    SM -->|"pandas read_excel / to_excel"| Books
    VOL -->|"pandas read_excel"| VolStore
    VOL -->|"pandas read_excel"| APIData
    PL -->|"pandas read_excel"| APIData
    API -->|"yfinance.download → to_excel"| APIData
```

---

## 3. Data Pipeline

```mermaid
flowchart LR
    subgraph Sources["External Data Sources"]
        YF_FX["Yahoo Finance\nEURUSD=X\nDaily OHLC"]
        YF_SB["Yahoo Finance\nSB=F\nDaily close prices"]
        XLS_VOL["Barchart Cmdty\nVol*.xlsx\nImplied Vol Smiles\n(manual export)"]
        XLS_POS["book.xlsx\nclosed_book.xlsx\nPosition Store\n(manual entry)"]
    end

    subgraph Ingestion["Ingestion & Parsing"]
        API_PIPE["API_intern.py\nScheduled pipeline\n(Windows Task Scheduler)\nyfinance.download()"]
        IO["SavingsManagement\nread_excel · dtype enforcement\ndate parsing · account routing"]
        PARSE_VOL["vol.py\nColumn remapping\nStrike / Delta extraction\nExpiry tagging"]
        PARSE_API["vol.py / PnLComputation.py\nread_excel(FX.xlsx)\nread_excel(HistVolSB.xlsx)"]
    end

    subgraph Compute["Quantitative Processing"]
        DF_POS[("DataFrame\nOpen / Closed\nPositions")]
        DF_VOL[("DataFrame\nImplied Vol\nSurface Panel")]
        DF_FX[("DataFrame\nEUR/USD rate\nfor P&L conversion")]
        DF_RV[("DataFrame\nSB=F prices\n20d Realized Vol")]

        TTM["TTM Computation\nACT/365 · ICE First-Notice Dates"]
        BLACK76["Black-76 Pricing Engine\nper-instrument vectorized pricing"]
        GREEKS["Greeks Computation\nΔ Γ ν Θ ρ · Vanna · Volga · Charm"]
        EXPLAIN["P&L Attribution Engine\nΔ PnL · Γ PnL · ν PnL · Θ PnL · Residual"]
        RV_COMP["Realized Vol\nstd(log-returns, 20d) × √252"]
        SMILE["Smile Analytics\nATM IV · RR · BF · Skew · Curvature"]
        SURFACE["3D Surface Interpolation\nStrike × Expiry × IV"]
        MISPRICE["Mispricing Map\nIV(K) − IV_ATM  per expiry"]
    end

    subgraph Presentation["Streamlit UI Layer"]
        UI_BOOK["Main Book\nGreeks tables · Delta/Gamma/Vega/Theta charts\nHedge advisor · Live PnL"]
        UI_PNL["P&L Reports\nEquity curve · Monthly bars\nPerformance KPIs · EUR conversion"]
        UI_VOL["Vol Tools\nSmile panel · Term structure\nSkew metrics · 3D surface\nIV vs 20d RV comparison"]
        UI_PRICER["Strategy Pricer\nMulti-leg builder · Per-leg Greeks"]
    end

    YF_FX -->|"yfinance (14d)"| API_PIPE
    YF_SB -->|"yfinance (1y)"| API_PIPE
    API_PIPE -->|"to_excel"| PARSE_API
    XLS_VOL -->|"read_excel"| PARSE_VOL
    XLS_POS -->|"read_excel"| IO

    IO --> DF_POS
    PARSE_VOL --> DF_VOL
    PARSE_API --> DF_FX & DF_RV

    DF_POS --> TTM --> BLACK76
    DF_VOL -->|"σ(K, T)"| BLACK76

    BLACK76 --> GREEKS --> UI_BOOK
    BLACK76 --> EXPLAIN --> UI_BOOK
    GREEKS --> UI_PRICER

    DF_POS --> EXPLAIN
    DF_POS --> UI_PNL
    DF_FX --> UI_PNL

    DF_RV --> RV_COMP --> UI_VOL
    DF_VOL --> SMILE --> UI_VOL
    DF_VOL --> SURFACE --> UI_VOL
    DF_VOL --> MISPRICE --> UI_VOL
```

---

## 4. Market Data Pipeline — API_intern.py

```mermaid
flowchart TD
    subgraph Trigger["Scheduled Trigger"]
        SCHED["Windows Task Scheduler\nBusiness days · 08:00"]
    end

    subgraph Pipeline["API_intern.py — Sequential Steps"]
        S1["Step 1 — EUR/USD\nyfinance.download('EURUSD=X', period='14d')\nFields: Open · High · Low · Close · Volume"]
        SLEEP["sleep(3s)\nYahoo Finance rate-limiting"]
        S2["Step 2 — Sugar #11\nyfinance.download('SB=F', period='1y')\nFields: Open · High · Low · Close · Volume"]
        COMPUTE["Realized Vol Computation\nrets = close.pct_change()\nvol_CtoC_20d = rets.rolling(20).std() × √252"]
    end

    subgraph Output["Outputs (API_data/)"]
        FX_OUT["FX.xlsx\nEUR/USD daily OHLC\n(last 14 days, rolling)"]
        SB_OUT["HistVolSB.xlsx\nSB=F daily close prices\nlog-returns · 20d annualized RV"]
    end

    subgraph Consumers["Downstream Consumers"]
        C1["PnLComputation.py\nEUR/USD latest rate\n→ P&L in EUR"]
        C2["vol.py\nSB=F price history\n20d RV vs ATM IV chart"]
    end

    SCHED --> S1 --> SLEEP --> S2 --> COMPUTE
    S1 -->|"to_excel"| FX_OUT
    COMPUTE -->|"to_excel"| SB_OUT
    FX_OUT --> C1
    SB_OUT --> C2
```

---

## 5. Pricing Model — Black-76

```mermaid
flowchart TD
    subgraph Inputs["Model Inputs"]
        IN["F  — Futures price (¢/lb, market)\nK  — Strike price\nT  — Time to maturity  [ACT/365]\nr  — Risk-free rate (default 2%)\nσ  — Implied volatility  [smile interpolated]\ntype — call | put | fut"]
    end

    subgraph Intermediates["Intermediate Computations"]
        D1["d₁ = [ ln(F/K) + ½σ²T ] / σ√T"]
        D2["d₂ = d₁ − σ√T"]
        DISC["Discount factor = e^(−rT)"]
    end

    subgraph Pricing["Option Price"]
        CALL_PRICE["Call = e^(−rT) · [ F·N(d₁) − K·N(d₂) ]"]
        PUT_PRICE["Put  = e^(−rT) · [ K·N(−d₂) − F·N(−d₁) ]"]
    end

    subgraph Greeks["First & Second Order Greeks"]
        G1["Δ (Delta)   = e^(−rT) · N(d₁)"]
        G2["Γ (Gamma)   = e^(−rT) · N'(d₁) / (F·σ·√T)"]
        G3["ν (Vega)    = F · e^(−rT) · N'(d₁) · √T"]
        G4["Θ (Theta)   = −[F·σ·e^(−rT)·N'(d₁)] / (2√T·252)"]
        G5["ρ (Rho)     = −T · option_price"]
        G6["Vanna        = −e^(−rT) · N'(d₁) · d₂/σ"]
        G7["Volga        = F · e^(−rT) · N'(d₁) · √T · d₁·d₂/σ"]
        G8["Charm        = −e^(−rT) · N'(d₁) · [2rT − d₂·σ·√T] / (2T·σ·√T)"]
    end

    subgraph PnLExplain["P&L Attribution (Taylor Expansion)"]
        PNL["PnL ≈  Δ·ΔF  +  ½Γ·ΔF²  +  ν·Δσ  +  Θ·Δt  +  residual"]
    end

    IN --> D1 & DISC
    D1 --> D2
    D1 & D2 & DISC --> CALL_PRICE & PUT_PRICE
    D1 & D2 & DISC --> G1 & G2 & G3 & G4 & G5 & G6 & G7 & G8
    G1 & G2 & G3 & G4 --> PNL
```

---

## 6. Session State & Reactivity Model

```mermaid
flowchart TD
    subgraph Init["Initialization (first load or account change)"]
        LOAD["load_open_positions(account_id)"]
        TTM_C["add_ttm_column(valuation_date)"]
        VOL_MAP["df['vol'] = expiry.map(DEFAULT_VOL)"]
        MULT["df['contract_multiplier'] = 112_000"]
        BUILD["build_greeks_dataframe(F_market, r=0.02)"]
    end

    subgraph State["st.session_state  ·  In-Memory Cache"]
        SS1["positions  — enriched DataFrame with Greeks"]
        SS2["F_market   — {expiry: futures_price}"]
        SS3["current_account  — active account id"]
        SS4["valuation_date   — pricing date"]
    end

    subgraph Reactivity["Reactivity Triggers"]
        T1["Account selector change"]
        T2["Valuation date change"]
        T3["Futures price slider update"]
    end

    subgraph Pages["Downstream Consumers"]
        P1["Main Book — Greeks, Hedge, PnL"]
        P4["Strategy Pricer — per-leg pricing"]
    end

    LOAD --> TTM_C --> VOL_MAP --> MULT --> BUILD
    BUILD --> SS1
    T1 & T2 --> LOAD
    T3 --> SS2

    SS1 & SS2 --> P1 & P4
    SS3 --> T1
    SS4 --> T2
```

---

## 7. Volatility Surface Construction

```mermaid
flowchart LR
    subgraph Raw["Raw Data — per expiry file\n(Barchart Cmdty manual export)"]
        FILE["Vol{X}barchart.xlsx\nDelta_Call · ImplV_Call · Strike\nImplV_Put · Delta_Put"]
    end

    subgraph Parse["Parsing & Normalization"]
        REMAP["Column remapping\n(Unnamed: x → semantic names)"]
        ATAG["Expiry tag extraction\nfrom filename → H/K/N/V"]
        FMAP["ATM forward injection\nF_market[expiry]"]
    end

    subgraph Panel["Unified Vol Panel"]
        DF["panel DataFrame\n[expiry · strike · delta_call · iv_call · iv_put · delta_put]"]
    end

    subgraph Analytics["Surface Analytics"]
        ATM["ATM IV — interpolated at F"]
        RR["Risk Reversal\nRR_25 = IV_25C − IV_25P\nRR_10 = IV_10C − IV_10P"]
        BF["Butterfly\nBF_25 = ½(IV_25C + IV_25P) − ATM\nBF_10 = ½(IV_10C + IV_10P) − ATM"]
        SLOPE["Smile Slopes\nslope_left · slope_right"]
        CURV["Curvature\nBF proxy at selected Δ"]
        SURF["3D Interpolation\nStrike × T axis → Plotly mesh"]
        HEAT["Mispricing Heatmap\nIV(K) − ATM_IV  per expiry"]
        RV["Realized Vol Overlay\n20d close-to-close vs ATM IV\nsource: API_data/HistVolSB.xlsx"]
    end

    FILE --> REMAP --> ATAG --> FMAP --> DF
    DF --> ATM & RR & BF & SLOPE & CURV & SURF & HEAT
    RV -.->|"HistVolSB.xlsx"| HEAT
```

---

## 8. Contract & Expiry Reference

| Code | Month   | First-Notice Rule                              |
|------|---------|------------------------------------------------|
| H    | March   | Last business day of the preceding month       |
| K    | May     | Last business day of the preceding month       |
| N    | July    | Last business day of the preceding month       |
| V    | October | Last business day of the preceding month       |

**Contract specs:** SB · ICE Futures US (IFUS) · 112,000 lbs per lot · US cents / lb · Tick 0.01 ¢/lb · Tick value USD 11.20

**Coverage:** H26 (March 2026) through V34 (October 2034) — first-notice dates hardcoded in `EXPIRY_DATES`.

---

## 9. Module Responsibility Matrix

| Module | Responsibility | Key Functions |
|---|---|---|
| `Cockpit.py` | Orchestration, routing, session state, UI layout | Page dispatch · `st.session_state` management · market input widgets |
| `GreeksManagement.py` | Black-76 pricing, Greeks, hedge advisor, PnL explain | `build_greeks_dataframe` · `portfolio_delta_by_expiry` · `compute_pnl_explain` · `delta_hedge_action_by_expiry` |
| `PnLComputation.py` | Realized P&L, EUR conversion, performance metrics | `build_daily_pnl_series` · `compute_sharpe` · `compute_max_drawdown` · `compute_pnl_by_year` |
| `vol.py` | Vol surface construction, smile analytics, RV vs IV | `build_smile_panel_from_excels` · `compute_skew_metrics` · `plot_vol_surface` · `compute_vol_mispricing_map` |
| `SavingsManagement.py` | Excel I/O, account-level data access | `load_open_positions` · `save_open_positions` · `load_closed_positions` |
| `API_intern.py` | Scheduled market data ingestion (yfinance) | `download EURUSD=X → FX.xlsx` · `download SB=F → HistVolSB.xlsx` · `compute vol_CtoC_20d` |

---

## 10. Account & Portfolio Structure

```mermaid
graph LR
    subgraph Accounts["Managed Accounts"]
        A1["95135"]
        A2["95136"]
        A3["95137"]
    end

    subgraph Instruments["Instrument Types"]
        FUT["fut — Futures"]
        CALL["call — Call Options"]
        PUT["put — Put Options"]
    end

    subgraph Expiries["Active Expiry Cycle  ·  ICE SB"]
        E1["H  Mar"]
        E2["K  May"]
        E3["N  Jul"]
        E4["V  Oct"]
    end

    A1 & A2 & A3 --> FUT & CALL & PUT
    FUT & CALL & PUT --> E1 & E2 & E3 & E4
```

---

## 11. Known Constraints & Design Decisions

| Area | Decision | Rationale |
|---|---|---|
| Persistence | Excel workbooks (no database) | Zero-infrastructure deployment · audit-friendly flat files |
| Pricing model | Black-76 with flat vol per expiry (default) | Industry standard for commodity options · smile loaded from Barchart when available |
| Vol source | Barchart Cmdty manual export (`.xlsx`) | No live IV API · vol data requires manual refresh |
| Market data | Yahoo Finance via `yfinance` (SB=F, EURUSD=X) | Free, automated daily feed for prices and realized vol |
| Vol interpolation | Linear interpolation across strikes within each expiry | Sufficient for risk monitoring · no-arbitrage constraints not enforced |
| RV computation | 20-day close-to-close, annualized (ACT/252) | Standard short-term realized vol benchmark vs ATM IV |
| Session state | `st.session_state` as in-memory cache | Avoids recomputing Greeks on every widget interaction |
| Deployment | `streamlit run Cockpit.py` — single process | Internal single-user tool · no concurrency requirements |
| Data scheduler | Windows Task Scheduler (`API_intern.py`) | Simple local automation · not portable to macOS/Linux |
| File paths | Dual-path (macOS / Windows) hardcoded | Multi-environment support · must be updated manually on new deployments |

---

*Source: `Cockpit.py` · `GreeksManagement.py` · `PnLComputation.py` · `vol.py` · `SavingsManagement.py` · `API_intern.py`*
