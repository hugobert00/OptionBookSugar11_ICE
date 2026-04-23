from __future__ import annotations
#=====================
#Cockpit of the dashboard 
#Here is the main cockpit of the dashboard, here is the page in which you can manage the page's organisation and display 
#All the functions and dependencies are available in the joined file and precisely called in this part. 
#The book dash board is made the simpliest way as possible in order to keep over time
# Disclaimer : The chosen way to build the dashboard is using Streamlit, it seems to be consistent over time, 
#however it is possible that new updates on streamlit mess with this beutiful system 
#You can find all the information needed for maintenance on : https://streamlit.io
#For any questions you can email me at (try to answer the fast as I can): hugo.berthelier@edhec.com
#=====================

import streamlit as st
import pandas as pd
import numpy as np
import os
import requests as r
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta, date 
import math
from pathlib import Path


#functions imports 
from SavingsManagement import load_open_positions, save_open_positions
from GreeksManagement import (add_ttm_column,
                              build_greeks_dataframe,
                              portfolio_delta_by_expiry,
                              plot_delta_vs_future_subplots,
                              hedge_cash_cost_by_expiry,
                              delta_hedge_action_by_expiry,
                              portfolio_gamma_by_expiry,
                              plot_gamma_vs_future_subplots,
                              portfolio_vega_by_expiry,
                              plot_vega_vs_future_subplots,
                              portfolio_theta_by_expiry,
                              plot_theta_vs_future_subplots,
                              compute_live_pnl,
                              compute_pnl_explain,
                              get_expiry_date,
                              bs76_price)

from PnLComputation import (
    load_closed_positions,
    compute_line_pnl,
    build_daily_pnl_series,
    compute_pnl_by_month,
    compute_pnl_by_expiry,
    compute_closed_pnl,
    compute_pnl_by_year,
    build_daily_pnl_series_by_year,
    compute_returns,
    compute_max_drawdown,
    #compute_cash_burn,
    compute_sharpe,
)

from vol import (
    build_smile_panel_from_excels,
    plot_smiles_panel,
    plot_vol_surface,
    compute_atm_term_structure,
    plot_atm_term_structure,
    compute_skew_metrics,
    plot_skew_bars,
    compute_smile_shape_metrics,
    plot_shape_lines,
    compute_vol_mispricing_map,
    plot_vol_mispricing_heatmap,
)


sugar11_contract_info = {
    "Sugar No. 11 NY": {
        "product_code": "SB",
        "contract_size": 112000,
        "unit": "US cents/lb",
        "currency": "USD",
        "tick_size": 0.01,
        "tick_value": 11.20,
        "expiration_months": ["H", "K", "N", "V"],
        "termination": "Last business day of the month preceding the delivery month"
    }
}

accounts = {
    "95135":{
        "Client_id" : 95135,
        "Client_name": "nom1"
    },
    "95136":{
        "Client_id" : 95136,
        "Client_name": "nom2"
    },
    "95137":{
        "Client_id" : 95137,
        "Client_name": "nom2"
    }
}


DEFAULT_VOL = {
    "H27": 0.20,
    "K26": 0.20,
    "N26": 0.20,
    "V26": 0.21,
    "H27": 0.20,
    "K27": 0.21,
    "N27": 0.22,
    "V27": 0.22

}

BASE_PATH_3 = Path("C:/PricerLb/PricerLBSugar#11/vol/")

FILENAMES = [
    
    "VolHbarchart.xlsx",
    "VolKbarchart.xlsx",
    "VolNbarchart.xlsx",
    "VolVbarchart.xlsx"
]

COLUMN_MAPPING = {
    "Unnamed: 0": "Delta_Call",
    "Unnamed: 1": "ImplV_Call",
    "Unnamed: 6": "Strike",
    "Unnamed: 11": "ImplV_Put",
    "Unnamed: 12": "Delta_Put",
}

builded_strategies = {
    "None (Manual Input)": [{"Type": "Call", "Quantity": 1, "Strike/fut price": 15}],
    "Call Spread": [{"Type": "Call", "Quantity": 1, "Strike/fut price": 15},
                     {"Type": "Call", "Quantity": -1, "Strike/fut price": 15.5}],
    "Put Spread": [{"Type": "Put", "Quantity": 1, "Strike/fut price": 15},
                    {"Type": "Put", "Quantity": -1, "Strike/fut price": 14.5}],
    "Short Call Spread":[{"Type": "Call", "Quantity": -1, "Strike/fut price": 15},
                     {"Type": "Call", "Quantity": 1, "Strike/fut price": 15.5}],
    "Short Put Spread":[{"Type": "Put", "Quantity": -1, "Strike/fut price": 15},
                    {"Type": "Put", "Quantity": 1, "Strike/fut price": 14.5}],
    "Covered Write": [{"Type": "fut", "Quantity": 1, "Strike/fut price": 15},
                       {"Type": "Call", "Quantity": -1, "Strike/fut price": 15}],
    "Protective Put": [{"Type": "fut", "Quantity": 1, "Strike/fut price": 15},
                        {"Type": "Put", "Quantity": 1, "Strike/fut price": 15}],
    "Long Straddle": [{"Type": "Call", "Quantity": 1, "Strike/fut price": 15},
                       {"Type": "Put", "Quantity": 1, "Strike/fut price": 15}],
    "Long Strangle": [{"Type": "Call", "Quantity": 1, "Strike/fut price": 15.5},
                       {"Type": "Put", "Quantity": 1, "Strike/fut price": 15}],
    "Short Straddle": [{"Type": "Call", "Quantity": -1, "Strike/fut price": 15},
                        {"Type": "Put", "Quantity": -1, "Strike/fut price": 15}],
    "Short Strangle": [{"Type": "Call", "Quantity": -1, "Strike/fut price": 15.5},
                       {"Type": "Put", "Quantity": -1, "Strike/fut price": 15}],
    "Long Call Butterfly": [{"Type": "Call", "Quantity": 1, "Strike/fut price": 14.5},
                             {"Type": "Call", "Quantity": -2, "Strike/fut price": 15},
                             {"Type": "Call", "Quantity": 1, "Strike/fut price": 15.5}],
    "Short Call Butterfly": [{"Type": "Call", "Quantity": -1, "Strike/fut price": 14.5},
                              {"Type": "Call", "Quantity": 2, "Strike/fut price": 15},
                              {"Type": "Call", "Quantity": -1, "Strike/fut price": 15.5}],
}




#--------------------------------------
#Dashboard construction 
#--------------------------------------
st.sidebar.image('logo_feedalliance_couleur1.png')
st.sidebar.title("Menu")

Menu =st.sidebar.selectbox("Which page would you access to ?", ('Main Book', 'Volatility tools', 'Pricer - Strategy', 'Closed Positions & PNL Reports'))
st.header(Menu)

#Cockpit page 
if Menu == 'Main Book':
    selected_account = st.sidebar.selectbox("Select an account", list(accounts.keys()))
    st.write(f'Welcome on your Sugar #11 Book Laurent!')
    st.subheader(f'Sugar #11 Book overview - Opened positions - Acc:{selected_account}')
    st.sidebar.subheader("Market inputs")
    valuation_date = st.sidebar.date_input("Valuation date",value=date.today())
    
    if "F_market" not in st.session_state:
        st.session_state["F_market"] = {
            "H27": 15.50,
            "K26": 15.50,
            "N26": 15.50,
            "V26": 16.00,
            "K27": 16.00,
            "N27": 16.00,
            "V27": 16.00
        }

    for expiry in st.session_state["F_market"]:
        st.session_state["F_market"][expiry] = st.sidebar.number_input(
            f"Future price {expiry}",
            value=st.session_state["F_market"][expiry],
            step=1.0
        )

    if (
    "positions" not in st.session_state
    or st.session_state.get("current_account") != selected_account
    or st.session_state.get("valuation_date") != valuation_date
    ):

        df = load_open_positions(selected_account)
        
        
        df = add_ttm_column(df, today=valuation_date)
        df["vol"] = df["expiry"].map(DEFAULT_VOL)
        df["contract_multiplier"] = 112000

        st.write(df)
        df = build_greeks_dataframe(
            df,
            F_market=st.session_state["F_market"],
            r=0.02
        )
        st.write("Greeks :")
        st.session_state["positions"] = df

        

        st.dataframe(
            df[
                [
                    "date", "type", "strike", "expiry", "quantity",
                    "delta", "gamma", "vega", "theta",
                    "rho", "vanna", "volga", "charm"
                ]
            ],
            width= 'stretch'
        )

    with st.expander("📊 Delta by maturity", expanded=True):

        df_positions = st.session_state["positions"]

        st.subheader("Delta by maturity")

        delta_by_expiry = portfolio_delta_by_expiry(df_positions)

        st.dataframe(
            delta_by_expiry,
            width='stretch'
        )

        # ----------------------------
        st.subheader("Delta vs future price")

        expiries = delta_by_expiry["expiry"].tolist()

        fig = plot_delta_vs_future_subplots(
            df=df_positions,
            expiries=expiries,
            F_market=st.session_state["F_market"],
            F_range_pct=0.10,
            price_steps=40
        )

        st.plotly_chart(fig, width='stretch')


        # ----------------------------
        st.subheader("Delta hedge actions")

        hedge_actions = delta_hedge_action_by_expiry(delta_by_expiry)

        st.dataframe(
            hedge_actions,
            width='stretch'
        )

        # ----------------------------
        st.subheader("Hedge cost")

        hedge_costs = hedge_cash_cost_by_expiry(
            hedge_actions_df=hedge_actions,
            F_market=st.session_state["F_market"],
            contract_multiplier=112000
        )

        st.dataframe(
            hedge_costs,
            width='stretch'
        )

        # ----------------------------
        total_delta = delta_by_expiry["delta_expiry"].sum()
        total_notional = hedge_costs["hedge_notional"].abs().sum()

        col1, col2 = st.columns(2)
        col1.metric("Total Delta (contracts)", f"{total_delta:,.1f}")
        col2.metric("Total Hedge Notional (USD)", f"{total_notional:,.0f}")

    with st.expander("📊 Gamma by maturity", expanded=False):

        df_positions = st.session_state["positions"]

        st.subheader("Gamma by maturity")

        gamma_by_expiry = portfolio_gamma_by_expiry(df_positions)

        st.dataframe(
            gamma_by_expiry,
            width='stretch'
        )

        # ----------------------------
        st.subheader("Gamma vs future price")

        expiries = gamma_by_expiry["expiry"].tolist()

        fig = plot_gamma_vs_future_subplots(
            df=df_positions,
            expiries=expiries,
            F_market=st.session_state["F_market"],
            F_range_pct=0.10,
            price_steps=40
        )

        st.plotly_chart(fig, width='stretch')

        # ----------------------------
        total_gamma = gamma_by_expiry["gamma_expiry"].sum()

        st.metric(
            "Total Gamma (contracts / price unit)",
            f"{total_gamma:,.6f}"
        )

    with st.expander("📊 Vega by maturity", expanded=False):

        df_positions = st.session_state["positions"]

        st.subheader("Vega by maturity")

        vega_by_expiry = portfolio_vega_by_expiry(df_positions)

        st.dataframe(
            vega_by_expiry,
            width='stretch'
        )

        # ----------------------------
        st.subheader("Vega vs future price")

        expiries = vega_by_expiry["expiry"].tolist()

        fig = plot_vega_vs_future_subplots(
            df=df_positions,
            expiries=expiries,
            F_market=st.session_state["F_market"],
            F_range_pct=0.10,
            price_steps=40
        )

        st.plotly_chart(fig, width='content')

        # ----------------------------
        total_vega = vega_by_expiry["vega_expiry"].sum()

        st.metric(
            "Total Vega (contracts / vol point)",
            f"{total_vega:,.1f}"
        )

    with st.expander("⏳ Theta by maturity", expanded=False):

            df_positions = st.session_state["positions"]

            st.subheader("Theta by maturity (USD / day)")

            theta_by_expiry = portfolio_theta_by_expiry(df_positions)

            st.dataframe(
                theta_by_expiry,
                width='stretch'
            )

            # ----------------------------
            st.subheader("Theta vs future price")

            expiries = theta_by_expiry["expiry"].tolist()

            fig = plot_theta_vs_future_subplots(
                df=df_positions,
                expiries=expiries,
                F_market=st.session_state["F_market"],
                F_range_pct=0.10,
                price_steps=40
            )

            st.plotly_chart(fig, width='stretch')

            # ----------------------------
            total_theta = theta_by_expiry["theta_expiry"].sum()

            st.metric(
                "Total Theta (USD / day)",
                f"{total_theta:,.0f}"
            )

    with st.expander("💰 Live PnL", expanded=True):

            df_positions = st.session_state["positions"]

            # --- Reference markets (yesterday / entry)
            F_ref = {k: v for k, v in st.session_state["F_market"].items()}
            vol_ref = {exp: DEFAULT_VOL[exp] for exp in F_ref}

            # --- Live PnL
            df_positions = compute_live_pnl(
                df_positions,
                F_market=st.session_state["F_market"]
            )

            # --- PnL Explain
            df_positions = compute_pnl_explain(
                df_positions,
                F_market=st.session_state["F_market"],
                F_ref=F_ref,
                vol_ref=vol_ref
            )

            # ----------------------------
            st.subheader("PnL by position")

            st.dataframe(
                df_positions[
                    [
                        "date", "type", "expiry", "quantity",
                        "live_pnl"
                    ]
                ],
                width='stretch'
            )

            # ----------------------------
            st.subheader("PnL Explain")

            pnl_explain_cols = [
                "pnl_delta",
                "pnl_gamma",
                "pnl_vega",
                "pnl_theta",
                "pnl_residual"
            ]

            totals = df_positions[pnl_explain_cols].sum()

            col1, col2, col3, col4, col5 = st.columns(5)

            col1.metric("Δ PnL", f"{totals['pnl_delta']:,.0f} USD")
            col2.metric("Γ PnL", f"{totals['pnl_gamma']:,.0f} USD")
            col3.metric("Vega PnL", f"{totals['pnl_vega']:,.0f} USD")
            col4.metric("Theta PnL", f"{totals['pnl_theta']:,.0f} USD")
            col5.metric("Residual", f"{totals['pnl_residual']:,.0f} USD")

            # ----------------------------
            st.subheader("Total Live PnL")

            total_pnl = df_positions["live_pnl"].sum()

            st.metric(
                "Total Live PnL (EUR)",
                f"{total_pnl:,.0f}"
            )

    #Volume interest on each strike 
    #bar plot that shows the volumes of calls and puts present on each strike 



    st.markdown("### Contract specifications")
    st.markdown("""
    - **Product**: SB - Sugar #11
    - **Multiplier**: 112 000
    - **Currency**: US cents / lbs
    - **Model**: Black-76
    - **TTM**: real exchange expiry dates
    """)

#Close Position & PNL Reports page
if Menu == 'Closed Positions & PNL Reports':
    selected_account = st.sidebar.selectbox("Select an account", list(accounts.keys()))
    st.write(f'Welcome on your Rapseed PnL report Laurent! You have selected {selected_account}.')
    if (
    "positions" not in st.session_state
    or st.session_state.get("current_account") != selected_account
    ):

        df = load_closed_positions(selected_account)
        df = compute_line_pnl(df)
        if df.empty : 
             st.warning("No closed positions available for this account.")
             st.stop()

        # ===============================
        # Daily / Monthly aggregates
        # ===============================
        daily_pnl = build_daily_pnl_series(df)
        monthly_pnl = compute_pnl_by_month(df)
        pnl_by_expiry = compute_pnl_by_expiry(df)
        summary = compute_closed_pnl(df)

        # ===============================
        # Yearly / Expiries aggregates
        # ===============================


        pnl_by_year = compute_pnl_by_year(df)
        daily_pnl_ytd = build_daily_pnl_series_by_year(df)



        # ===============================
        # Equity curve & risk metrics
        # ===============================
        equity_curve = daily_pnl.set_index("date")["cum_pnl"]

        returns = compute_returns(equity_curve)
        max_dd = compute_max_drawdown(equity_curve)
        #cash_burn = compute_cash_burn(monthly_pnl)
        sharpe = compute_sharpe(returns)




    # ===============================
    # Yearly PnL evolution
    # ===============================
    st.subheader("PnL overview")

    tab_global, tab_yearly = st.tabs(["Global (since inception)", "By year"])

    with tab_global:
        st.write("Cumulative realized PnL since inception (closed trades).")
        st.line_chart(daily_pnl.set_index("date")[["cum_pnl"]], height=350)

    with tab_yearly:
        st.write("PnL by calendar year and YTD equity curve (reset each Jan 1st).")

        st.bar_chart(pnl_by_year.set_index("year")[["pnl"]], height=250)

        years = [int(y) for y in pnl_by_year["year"].dropna().unique()]
        years = sorted(years)
        if years:
            selected_year = st.selectbox("Select a year", years, index=len(years)-1)

            ytd = daily_pnl_ytd[daily_pnl_ytd["year"] == selected_year].copy()
            if not ytd.empty:
                ytd_series = ytd.set_index("date")[["cum_pnl_ytd"]]
                st.line_chart(ytd_series, height=300)
            else:
                st.info("No daily data for selected year.")
        else:
            st.info("No yearly data available.")


    st.subheader("Monthly PnL : ")
    #here we put the bar chart of the PnL of each month 
    st.bar_chart(
        monthly_pnl.set_index("month")[["pnl"]],
        height=300
    )

    st.subheader("PnL by expiry")
    st.bar_chart(
        pnl_by_expiry.set_index("expiry")[["pnl"]],
        height=300
    )

    with st.expander("PnL by expiry - details", expanded=False):
        st.dataframe(pnl_by_expiry, width='stretch')


    


    with st.expander("Closed positions", expanded=False):
         st.subheader("Closed position details : ")
         st.write(df)


    # ===============================
    # Performance metrics
    # ===============================
    st.subheader("Performance metrics")

    # Last year available
    last_year = int(pnl_by_year["year"].dropna().max()) if not pnl_by_year.empty else None

    # ---------- Ligne 1 : Global ----------
    col1, col2, col3 = st.columns(3)

    if last_year is not None:
        pnl_last_year = float(
            pnl_by_year.loc[pnl_by_year["year"] == last_year, "pnl"].iloc[0]
        )
        n_last_year = int(
            pnl_by_year.loc[pnl_by_year["year"] == last_year, "n_trades"].iloc[0]
        )

        col1.metric(
            f"Total PnL {last_year} (USD)",
            f"{pnl_last_year:,.0f}"
        )
    else:
        col1.metric(
            "PnL (Year)",
            "n/a"
        )

    col2.metric(
        "Number of trades",
        f"{summary['n_trades']}"
    )

    col3.metric(
        "Win rate",
        f"{summary['win_rate'] * 100:.1f} %"
    )

    # ---------- Ligne 2 : Risk / performance ----------
    col4, col5, col6 = st.columns(3)

    col4.metric(
        "Max drawdown",
        f"{max_dd * 100:.2f} %"
    )

    col5.metric(
        "Sharpe ratio",
        f"{sharpe:.2f}"
    )

    col6.metric(
        "Total Cumulated PnL (USD)",
         f"{summary['total_pnl']:,.0f}"
     )

    # ===============================
    # FX Exposure
    # ===============================
    st.subheader("FX Exposure (USD → EUR)")
    try:
        fx_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "API_data", "FX.xlsx")
        df_fx = pd.read_excel(fx_path, index_col=0, parse_dates=True)
        eurusd = float(df_fx["close"].dropna().iloc[-1])
        total_pnl_usd = summary["total_pnl"]
        total_pnl_eur = total_pnl_usd / eurusd

        col_fx1, col_fx2, col_fx3 = st.columns(3)
        col_fx1.metric("EUR/USD (dernière clôture)", f"{eurusd:.4f}")
        col_fx2.metric("Total PnL (USD)", f"{total_pnl_usd:,.0f}")
        col_fx3.metric("Total PnL (EUR)", f"{total_pnl_eur:,.0f}")
        st.caption("Sugar #11 est coté en USD — le PnL EUR est calculé au taux EUR/USD de la dernière clôture disponible.")
    except Exception as e:
        st.warning(f"Données FX non disponibles : {e}")

#Volatility page tools 
if Menu == 'Volatility tools':
    valuation_date = st.sidebar.date_input("Valuation date", value=date.today())

    st.subheader("Volatility smile and skewness")
    st.write("Volatility smile for Sugar #11 for all available expiries")

    # ----------------------------
    # Controls
    # ----------------------------
    x_mode_ui = st.selectbox(
        "Choose sticky strike or sticky delta",
        options=["Strike", "Delta (signé)", "Delta (absolu)"],
        index=0
    )
    x_mode = {
        "Strike": "strike",
        "Delta (signé)": "delta_signed",
        "Delta (absolu)": "delta_abs"
    }[x_mode_ui]

    available_expiries = sorted(st.session_state["F_market"].keys())
    selected_expiries = st.multiselect(
        "Expiries available",
        options=available_expiries,
        default=available_expiries
    )

    # ----------------------------
    # Load vols
    # ----------------------------
    panel = build_smile_panel_from_excels(
        base_path=BASE_PATH_3,
        filenames=FILENAMES,
        column_mapping=COLUMN_MAPPING,
        F_market=st.session_state["F_market"],
        year_suffix="26"
    )

    if panel.empty:
        st.warning("No implied vol data loaded (missing Excel files or expiry mapping).")
        st.stop()

    # Filtre panel sur expiries sélectionnées (important pour les métriques)
    panel_sel = panel[panel["expiry"].isin(selected_expiries)].copy()
    if panel_sel.empty:
        st.warning("No data for selected expiries.")
        st.stop()

    # ----------------------------
    # Smile plot
    # ----------------------------
    fig_smile = plot_smiles_panel(
        panel=panel_sel,
        x_mode=x_mode,
        expiries=selected_expiries,
        title="Implied vol smiles"
    )
    st.plotly_chart(fig_smile, width='stretch')

    with st.expander("Implied vol data", expanded=False):
        st.dataframe(panel_sel, width='stretch')

    st.divider()

    # ============================================================
    # (1) ATM term structure
    # ============================================================
    st.subheader("ATM Vol Term Structure")
    df_ts = compute_atm_term_structure(panel_sel, st.session_state["F_market"])
    st.plotly_chart(plot_atm_term_structure(df_ts, title="ATM IV term structure"), width='stretch')
    with st.expander("ATM term structure table", expanded=False):
        st.dataframe(df_ts, width='stretch')

    st.divider()

    # ============================================================
    # (2) Skew metrics: RR / BF / PutSkew for 25Δ and 10Δ
    # ============================================================
    st.subheader("Skew Metrics (10Δ / 25Δ)")

    df_skew = compute_skew_metrics(panel_sel, st.session_state["F_market"], deltas=(0.10, 0.25))
    with st.expander("Skew metrics table", expanded=False):
        st.dataframe(df_skew, width='stretch')

        c1, c2, c3 = st.columns(3)
        with c1:
            st.plotly_chart(plot_skew_bars(df_skew, metric="rr_25", title="25Δ Risk Reversal"), width='stretch')
        with c2:
            st.plotly_chart(plot_skew_bars(df_skew, metric="bf_25", title="25Δ Butterfly"), width='stretch')
        with c3:
            st.plotly_chart(plot_skew_bars(df_skew, metric="putskew_25", title="25Δ Put Skew (IV25P - ATM)"), width='stretch')

        st.divider()

    # ============================================================
    # (3) Smile slope & curvature (based on 25Δ by default)
    # ============================================================
    st.subheader("Smile Shape (Slopes & Curvature)")

    shape_delta = st.selectbox("Delta used for shape metrics", options=[0.10, 0.25], index=0)
    df_shape = compute_smile_shape_metrics(df_skew, d=float(shape_delta))

    k = int(round(float(shape_delta) * 100))
    cols_slopes = [f"slope_left_{k}", f"slope_right_{k}"]
    cols_curve = [f"curvature_{k}"]

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            plot_shape_lines(df_shape, cols=cols_slopes, title=f"Smile slopes ({k}Δ)"),
            width='stretch'
        )
    with c2:
        st.plotly_chart(
            plot_shape_lines(df_shape, cols=cols_curve, title=f"Smile curvature ({k}Δ)"),
            width='stretch'
        )

    with st.expander("Shape metrics table", expanded=False):
        st.dataframe(df_shape, width='stretch')

    st.divider()

    # ============================================================
    # 3D Surface
    # ============================================================
    st.subheader("3D Surface implied vol")
    fig_surface = plot_vol_surface(
        panel=panel_sel,
        valuation_date=valuation_date,
        expiries=selected_expiries,
        n_strikes=70,
        fill_across_expiries=True,
        title="Implied vol surface - ICE Sugar#11"
    )
    st.plotly_chart(fig_surface, width='stretch')

    st.divider()

    # ============================================================
    # (5) Vol Mispricing map vs ATM
    # ============================================================
    st.subheader("Vol Mispricing Map (IV - ATM)")
    df_map = compute_vol_mispricing_map(panel_sel, st.session_state["F_market"])
    fig_map = plot_vol_mispricing_heatmap(df_map, title="IV(K) - IV_ATM (vol points)")
    st.plotly_chart(fig_map, width='stretch')

    with st.expander("Mispricing map data", expanded=False):
        st.dataframe(df_map, width='stretch')

    st.divider()

    # ============================================================
    # Realized volatility & returns distribution (HistVolSB.xlsx)
    # ============================================================
    try:
        hvol_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "API_data", "HistVolSB.xlsx")
        df_hv = pd.read_excel(hvol_path, index_col=0, parse_dates=True)
        df_hv = df_hv.dropna(subset=["vol_CtoC_20d"])

        # — Realized vol curve —
        st.subheader("Realized Volatility — Close-to-Close 20d (annualised)")
        fig_rv = go.Figure()
        fig_rv.add_trace(go.Scatter(
            x=df_hv.index,
            y=(df_hv["vol_CtoC_20d"] * 100).round(2),
            mode="lines",
            name="HV 20d",
            line=dict(color="#00b4d8", width=2)
        ))
        fig_rv.update_layout(
            title="Sugar #11 — Realized Vol CtoC 20d (%)",
            xaxis_title="Date",
            yaxis_title="Realized Vol (%)",
            template="plotly_dark",
            hovermode="x unified"
        )
        st.plotly_chart(fig_rv, width='stretch')

        st.divider()

        # — Returns distribution —
        st.subheader("Close-to-Close Returns Distribution")
        rets = df_hv["rets"].dropna() * 100  # en %
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Histogram(
            x=rets.round(3),
            nbinsx=60,
            name="Daily returns",
            marker_color="#00b4d8",
            opacity=0.8
        ))
        fig_dist.update_layout(
            title="Sugar #11 — Distribution des returns CtoC (%)",
            xaxis_title="Return (%)",
            yaxis_title="Frequency",
            template="plotly_dark",
            bargap=0.05
        )
        st.plotly_chart(fig_dist, width='stretch')

        with st.expander("Realized vol data", expanded=False):
            st.dataframe(df_hv[["close", "rets", "vol_CtoC_20d"]].tail(60).sort_index(ascending=False), width='stretch')

    except Exception as e:
        st.warning(f"Realized vol data unavailable: {e}")

    st.divider()



    st.write("Disclaimer: all data are extracted from Barchart.com via Cmdty views and an internal API base on Yahoo Finance Data.")
    st.write("Please manually verify implied vol data (source files in /PricerLBSugar#11/vol).")


#--------------------------
#Pricer page building
#--------------------------


if Menu == 'Pricer - Strategy':

    st.subheader("Pricer - Build your strategy here - ICE Sugar #11")
    st.write("Welcome on your ICE Sugar #11 pricer Laurent - Please enter your strategy below :")
    st.sidebar.subheader("Market inputs")
    valuation_date = st.sidebar.date_input("Valuation date",value=date.today())
    st.sidebar.write("Market prices for each expiry are taken from the Main book page.")
    st.sidebar.subheader("Pre-builded strategies : ")
    selected_strategy = st.sidebar.selectbox("Select a strategy", list(builded_strategies.keys()))
    st.sidebar.write("You can customize in the code your default strategies :)")
    st.sidebar.subheader("Pricing model used : ")
    st.sidebar.write("A Black-76 model is used with a Local Vol Model to capture skew dynamics.")


    


    # # ── Market data ───────────────────────────────────────────────────────────────
    # if "F_market" not in st.session_state:
    #     st.session_state["F_market"] = {
    #         "F27": 320.00, "H26": 325.00, "K26": 328.00,
    #         "N26": 330.00, "Q26": 325.00, "U26": 320.00,
    #         "V26": 320.00, "Z26": 325.00
    #     }
    # F_mkt = st.session_state["F_market"]
    # available_expiries = list(F_mkt.keys())

    # # ── Vol panel (smile interpolation) ──────────────────────────────────────────
    # try:
    #     panel_pricer = build_smile_panel_from_excels(
    #         base_path=BASE_PATH_3,
    #         filenames=FILENAMES,
    #         column_mapping=COLUMN_MAPPING,
    #         F_market=F_mkt,
    #         year_suffix="26"
    #     )
    # except Exception:
    #     panel_pricer = pd.DataFrame()

    # def get_smile_vol(expiry, strike):
    #     """Interpolate implied vol from the smile panel at a given expiry/strike."""
    #     if panel_pricer.empty or expiry not in panel_pricer["expiry"].values:
    #         return DEFAULT_VOL.get(expiry, 0.20)
    #     dfe = (panel_pricer[panel_pricer["expiry"] == expiry]
    #            .dropna(subset=["Strike", "IV_Mid"])
    #            .sort_values("Strike"))
    #     if len(dfe) < 2:
    #         return DEFAULT_VOL.get(expiry, 0.20)
    #     return float(np.clip(np.interp(strike, dfe["Strike"].values, dfe["IV_Mid"].values), 0.01, 2.0))

    # def get_leg_ttm(expiry):
    #     """Time to maturity in years for an expiry code."""
    #     today = pd.to_datetime(valuation_date).date()
    #     return max((get_expiry_date(expiry) - today).days, 0) / 365.0

    # # ── Vectorized Black-76 (payoff / current-value charts) ──────────────────────
    # def _Ncdf(x):
    #     _verf = np.vectorize(math.erf)
    #     return 0.5 * (1.0 + _verf(x / np.sqrt(2)))

    # def bs76_vec(opt_type, F_arr, K, v, T, r=0.02):
    #     F_arr = np.asarray(F_arr, dtype=float)
    #     if T <= 0 or v <= 0 or K <= 0:
    #         return np.maximum(F_arr - K, 0) if opt_type == "c" else np.maximum(K - F_arr, 0)
    #     safe = np.where(F_arr > 0, F_arr, 1e-9)
    #     d1 = (np.log(safe / K) + 0.5 * v ** 2 * T) / (v * np.sqrt(T))
    #     d2 = d1 - v * np.sqrt(T)
    #     disc = math.exp(-r * T)
    #     if opt_type == "c":
    #         return disc * (F_arr * _Ncdf(d1) - K * _Ncdf(d2))
    #     return disc * (K * _Ncdf(-d2) - F_arr * _Ncdf(-d1))

    # # ── Session state ─────────────────────────────────────────────────────────────
    # if "strategy_legs" not in st.session_state:
    #     st.session_state["strategy_legs"] = []
    # if "pricer_last_strategy" not in st.session_state:
    #     st.session_state["pricer_last_strategy"] = "None (Manual Input)"

    # # ── Auto-load pre-built strategy when selectbox changes ───────────────────────
    # _TYPE_MAP = {"Call": "c", "Put": "p", "fut": "f"}
    # if (selected_strategy != "None (Manual Input)"
    #         and selected_strategy != st.session_state["pricer_last_strategy"]):
    #     _default_exp = available_expiries[0]
    #     _new_legs = []
    #     for _tpl in builded_strategies[selected_strategy]:
    #         _itype  = _TYPE_MAP.get(_tpl["Type"], "c")
    #         _strike = (float(F_mkt.get(_default_exp, 330.0))
    #                    if _itype == "f"
    #                    else float(_tpl["Strike/fut price"]))
    #         _qty = int(_tpl["Quantity"])
    #         _vol = get_smile_vol(_default_exp, _strike) if _itype != "f" else 0.0
    #         _new_legs.append({
    #             "type": _itype,
    #             "expiry": _default_exp,
    #             "strike": _strike,
    #             "quantity": _qty,
    #             "vol": round(_vol, 4),
    #             "T": get_leg_ttm(_default_exp),
    #             "contract_multiplier": 100
    #         })
    #     st.session_state["strategy_legs"] = _new_legs
    #     st.session_state["pricer_last_strategy"] = selected_strategy
    #     st.rerun()
    # elif selected_strategy == "None (Manual Input)":
    #     st.session_state["pricer_last_strategy"] = "None (Manual Input)"

    # # ── Leg builder form ──────────────────────────────────────────────────────────
    # st.write("Add and delete components of your strategy here :")
    # with st.form("add_leg_form", clear_on_submit=True):
    #     fc1, fc2, fc3, fc4 = st.columns([1.2, 1.5, 1.5, 1.2])
    #     _new_type   = fc1.selectbox("Type", ["Call", "Put", "Futures"])
    #     _new_expiry = fc2.selectbox("Expiry", available_expiries)
    #     _new_strike = fc3.number_input(
    #         "Strike / Fut entry price",
    #         value=float(F_mkt.get(available_expiries[0], 330.0)),
    #         step=1.0
    #     )
    #     _new_qty  = fc4.number_input("Quantity (neg = short)", value=1, step=1)
    #     _add_btn  = st.form_submit_button("Add leg")

    # if _add_btn:
    #     _itype = {"Call": "c", "Put": "p", "Futures": "f"}[_new_type]
    #     st.session_state["strategy_legs"].append({
    #         "type": _itype,
    #         "expiry": _new_expiry,
    #         "strike": float(_new_strike),
    #         "quantity": int(_new_qty),
    #         "vol": round(get_smile_vol(_new_expiry, _new_strike), 4) if _itype != "f" else 0.0,
    #         "T": get_leg_ttm(_new_expiry),
    #         "contract_multiplier": 100
    #     })
    #     st.rerun()

    # # ── Current legs display ──────────────────────────────────────────────────────
    # legs = st.session_state["strategy_legs"]
    # _LTYPE = {"c": "Call", "p": "Put", "f": "Futures"}
    # if legs:
    #     _hcols = st.columns([0.4, 1.0, 1.0, 1.2, 0.8, 1.4, 0.6])
    #     for _h, _lbl in zip(_hcols, ["#", "Type", "Expiry", "Strike", "Qty", "σ (smile)", ""]):
    #         _h.markdown(f"**{_lbl}**")
    #     _to_del = None
    #     for _i, _leg in enumerate(legs):
    #         _rc = st.columns([0.4, 1.0, 1.0, 1.2, 0.8, 1.4, 0.6])
    #         _rc[0].write(_i + 1)
    #         _rc[1].write(_LTYPE.get(_leg["type"], _leg["type"]))
    #         _rc[2].write(_leg["expiry"])
    #         _rc[3].write(f"{_leg['strike']:.1f}")
    #         _rc[4].write(f"{_leg['quantity']:+d}")
    #         _rc[5].write(f"{_leg['vol']*100:.2f}%" if _leg["type"] != "f" else "—")
    #         if _rc[6].button("Del", key=f"del_leg_{_i}"):
    #             _to_del = _i
    #     if _to_del is not None:
    #         st.session_state["strategy_legs"].pop(_to_del)
    #         st.rerun()
    #     _cc, _ = st.columns([1, 6])
    #     if _cc.button("Clear all"):
    #         st.session_state["strategy_legs"] = []
    #         st.rerun()
    # else:
    #     st.info("No legs yet. Add a leg above or select a pre-built strategy from the sidebar.")

    # # ── Pricing & visualisations (only when legs exist) ───────────────────────────
    # if legs:

    #     df_strat = pd.DataFrame([{
    #         "type":                _l["type"],
    #         "expiry":              _l["expiry"],
    #         "strike":              float(_l["strike"]),
    #         "quantity":            int(_l["quantity"]),
    #         "vol":                 float(_l["vol"]),
    #         "T":                   float(_l["T"]),
    #         "contract_multiplier": int(_l["contract_multiplier"])
    #     } for _l in legs])

    #     # Option premiums (futures → 0 upfront cost)
    #     def _leg_prem(row, r=0.02):
    #         _it = row["type"]
    #         if _it == "f":
    #             return 0.0
    #         _F = float(F_mkt.get(row["expiry"], 330.0))
    #         _K, _v, _T = row["strike"], row["vol"], row["T"]
    #         if _T <= 0 or _v <= 0:
    #             return max(_F - _K, 0) if _it == "c" else max(_K - _F, 0)
    #         return bs76_price(_it, _F, _K, _v, _T, r)

    #     df_strat["price"]       = df_strat.apply(_leg_prem, axis=1)
    #     df_strat["net_premium"] = (df_strat["price"]
    #                                * df_strat["quantity"]
    #                                * df_strat["contract_multiplier"])
    #     total_cost = df_strat["net_premium"].sum()

    #     # Greeks via existing Black-76 engine
    #     df_strat = build_greeks_dataframe(df_strat, F_mkt, r=0.02)

    #     # ── Details of the strategy ───────────────────────────────────────────────
    #     st.subheader("Details of the strategy :")
    #     with st.expander("Greeks of the strategy :", expanded=True):
    #         _disp = ["type", "expiry", "strike", "quantity", "vol", "T",
    #                  "price", "net_premium", "delta", "gamma", "vega", "theta"]
    #         st.dataframe(
    #             df_strat[_disp].style.format({
    #                 "vol": "{:.1%}", "T": "{:.3f}", "price": "{:.3f}",
    #                 "net_premium": "{:,.0f}", "delta": "{:.4f}",
    #                 "gamma": "{:.6f}", "vega": "{:.4f}", "theta": "{:.4f}"
    #             }),
    #             use_container_width=True
    #         )
    #         _m1, _m2, _m3, _m4 = st.columns(4)
    #         _m1.metric("Net Delta", f"{df_strat['delta'].sum():.4f}")
    #         _m2.metric("Net Gamma", f"{df_strat['gamma'].sum():.6f}")
    #         _m3.metric("Net Vega",  f"{df_strat['vega'].sum():.4f}")
    #         _m4.metric("Net Theta", f"{df_strat['theta'].sum():.4f}")

    #     # ── Cost of each leg ──────────────────────────────────────────────────────
    #     st.write("Cost of the full strategy :")
    #     with st.expander("Cost of each leg :", expanded=False):
    #         st.dataframe(
    #             df_strat[["type", "expiry", "strike", "quantity", "price", "net_premium"]]
    #             .style.format({"price": "{:.3f}", "net_premium": "{:,.0f}"}),
    #             use_container_width=True
    #         )
    #         st.metric("Net Strategy Cost (USD)", f"{total_cost:,.2f}")

    #     # ── Payoff & Profit Profile ───────────────────────────────────────────────
    #     st.subheader("Payoff & Profit Profile at Expiry")

    #     _ref_exp = df_strat["expiry"].iloc[0]
    #     _F_ref   = float(F_mkt.get(_ref_exp, 330.0))
    #     _F_range = np.linspace(_F_ref * 0.70, _F_ref * 1.30, 300)

    #     _payoff_exp  = np.zeros(len(_F_range))
    #     _current_val = np.zeros(len(_F_range))

    #     for _, _row in df_strat.iterrows():
    #         _it   = _row["type"]
    #         _K    = float(_row["strike"])
    #         _qty  = float(_row["quantity"])
    #         _mult = float(_row["contract_multiplier"])
    #         _v    = float(_row["vol"])
    #         _T    = float(_row["T"])
    #         if _it == "f":
    #             _pnl_f = _qty * _mult * (_F_range - _K)
    #             _payoff_exp  += _pnl_f
    #             _current_val += _pnl_f
    #         elif _it == "c":
    #             _payoff_exp  += _qty * _mult * np.maximum(_F_range - _K, 0)
    #             _current_val += _qty * _mult * bs76_vec("c", _F_range, _K, _v, _T)
    #         elif _it == "p":
    #             _payoff_exp  += _qty * _mult * np.maximum(_K - _F_range, 0)
    #             _current_val += _qty * _mult * bs76_vec("p", _F_range, _K, _v, _T)

    #     _profit_exp  = _payoff_exp  - total_cost
    #     _current_pnl = _current_val - total_cost

    #     fig_pay = go.Figure()
    #     fig_pay.add_trace(go.Scatter(
    #         x=_F_range, y=_payoff_exp,
    #         name="Intrinsic payoff (at expiry)",
    #         line=dict(color="rgba(255,255,255,0.45)", dash="dash", width=1.5)
    #     ))
    #     fig_pay.add_trace(go.Scatter(
    #         x=_F_range, y=_profit_exp,
    #         name="Profit at expiry",
    #         line=dict(color="#00e676", width=2.5)
    #     ))
    #     fig_pay.add_trace(go.Scatter(
    #         x=_F_range, y=_current_pnl,
    #         name="Current P&L (Black-76)",
    #         line=dict(color="#ff9800", width=2.5)
    #     ))
    #     fig_pay.add_hline(y=0, line_dash="dot", line_color="gray", line_width=1)
    #     fig_pay.add_vline(
    #         x=_F_ref, line_dash="dash", line_color="#64b5f6",
    #         annotation_text=f"F = {_F_ref:.1f}",
    #         annotation_position="top right"
    #     )
    #     fig_pay.update_layout(
    #         title="Payoff / Profit Profile",
    #         xaxis_title="Underlying price",
    #         yaxis_title="P&L (USD)",
    #         template="plotly_dark",
    #         legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    #         height=420
    #     )
    #     st.plotly_chart(fig_pay, use_container_width=True)

    #     # ── Greeks Profile vs Underlying Price ────────────────────────────────────
    #     st.subheader("Greeks Profile vs Underlying Price")

    #     _F_gr = np.linspace(_F_ref * 0.80, _F_ref * 1.20, 80)
    #     _gr   = {"Delta": [], "Gamma": [], "Vega": [], "Theta": []}

    #     for _F_s in _F_gr:
    #         _scale  = _F_s / _F_ref if _F_ref > 0 else 1.0
    #         _F_tmp  = {_exp: F_mkt[_exp] * _scale for _exp in F_mkt}
    #         _df_tmp = build_greeks_dataframe(df_strat.copy(), _F_tmp, r=0.02)
    #         _gr["Delta"].append(_df_tmp["delta"].sum())
    #         _gr["Gamma"].append(_df_tmp["gamma"].sum())
    #         _gr["Vega"].append(_df_tmp["vega"].sum())
    #         _gr["Theta"].append(_df_tmp["theta"].sum())

    #     _GREEK_CLR = {
    #         "Delta": "#64b5f6",
    #         "Gamma": "#a5d6a7",
    #         "Vega":  "#ffcc80",
    #         "Theta": "#ef9a9a"
    #     }

    #     def _greek_fig(gname):
    #         _fg = go.Figure()
    #         _fg.add_trace(go.Scatter(
    #             x=_F_gr, y=_gr[gname],
    #             mode="lines", name=gname,
    #             line=dict(color=_GREEK_CLR[gname], width=2)
    #         ))
    #         _fg.add_vline(x=_F_ref, line_dash="dash", line_color="#64b5f6")
    #         _fg.add_hline(y=0, line_dash="dot", line_color="gray", line_width=1)
    #         _fg.update_layout(
    #             title=gname,
    #             xaxis_title="Underlying price",
    #             yaxis_title=gname,
    #             template="plotly_dark",
    #             height=290,
    #             margin=dict(t=40, b=30, l=40, r=20)
    #         )
    #         return _fg

    #     _gc1, _gc2 = st.columns(2)
    #     _gc3, _gc4 = st.columns(2)
    #     _gc1.plotly_chart(_greek_fig("Delta"), use_container_width=True)
    #     _gc2.plotly_chart(_greek_fig("Gamma"), use_container_width=True)
    #     _gc3.plotly_chart(_greek_fig("Vega"),  use_container_width=True)
    #     _gc4.plotly_chart(_greek_fig("Theta"), use_container_width=True)





