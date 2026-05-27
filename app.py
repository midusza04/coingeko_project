"""
Cryptocurrency Market Analysis – Streamlit Application
Advanced Databases | Michał Dusza · Szymon Bugajski · Mateusz Basiura
"""

import sqlite3
import time
import warnings
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

warnings.filterwarnings("ignore")

# ── Constants ──────────────────────────────────────────────────────────────────
DB_PATH = "crypto_market.db"
BASE_URL = "https://api.coingecko.com/api/v3"
REQUEST_DELAY = 10  # seconds between calls (free-tier rate limit)

COINS = [
    {"id": "bitcoin",     "symbol": "BTC", "name": "Bitcoin"},
    {"id": "ethereum",    "symbol": "ETH", "name": "Ethereum"},
    {"id": "solana",      "symbol": "SOL", "name": "Solana"},
    {"id": "binancecoin", "symbol": "BNB", "name": "BNB"},
    {"id": "ripple",      "symbol": "XRP", "name": "XRP"},
]

METRIC_MAP = {
    "Price (USD)":           "price_usd",
    "Market Capitalization": "market_cap",
    "Trading Volume (24h)":  "total_volume",
}

PERIOD_MAP = {
    "Last 7 days":   7,
    "Last 30 days":  30,
    "Last 90 days":  90,
    "Last 180 days": 180,
    "Last 365 days": 365,
}

AGG_MAP = {
    "Mean":               "mean",
    "Maximum":            "max",
    "Minimum":            "min",
    "Last value":         "last",
    "Standard Deviation": "std",
}


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════════════

def create_database() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cryptocurrencies (
            id TEXT PRIMARY KEY, symbol TEXT NOT NULL, name TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS market_snapshots (
            record_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            crypto_id     TEXT NOT NULL,
            snapshot_date DATE NOT NULL,
            price_usd     REAL,
            market_cap    REAL,
            total_volume  REAL,
            UNIQUE(crypto_id, snapshot_date),
            FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(id)
        )
    """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_snapshots_date "
        "ON market_snapshots(snapshot_date)"
    )
    cur.execute("""
        CREATE TABLE IF NOT EXISTS market_current (
            record_id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            crypto_id                   TEXT    NOT NULL,
            collected_at                DATETIME NOT NULL,
            price_usd                   REAL, market_cap         REAL,
            total_volume                REAL, high_24h           REAL,
            low_24h                     REAL, price_change_24h   REAL,
            price_change_percentage_24h REAL, price_change_percentage_7d REAL,
            market_cap_rank             INTEGER, circulating_supply REAL,
            total_supply                REAL,  max_supply         REAL,
            ath                         REAL,  ath_change_percentage REAL,
            FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(id)
        )
    """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_current_collected_at "
        "ON market_current(collected_at)"
    )
    for coin in COINS:
        cur.execute(
            "INSERT OR IGNORE INTO cryptocurrencies (id, symbol, name) VALUES (?,?,?)",
            (coin["id"], coin["symbol"], coin["name"]),
        )
    conn.commit()
    conn.close()


@st.cache_data(ttl=60)
def load_snapshots() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT s.snapshot_date, s.price_usd, s.market_cap, s.total_volume,
               c.name, c.symbol
        FROM market_snapshots s
        JOIN cryptocurrencies c ON s.crypto_id = c.id
        ORDER BY s.snapshot_date
    """, conn)
    conn.close()
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
    return df


@st.cache_data(ttl=60)
def load_db_stats() -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    stats: dict = {}
    for tbl in ["cryptocurrencies", "market_snapshots", "market_current"]:
        stats[tbl] = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    row = cur.execute(
        "SELECT MIN(snapshot_date), MAX(snapshot_date) FROM market_snapshots"
    ).fetchone()
    stats["date_from"], stats["date_to"] = row
    conn.close()
    return stats


# ══════════════════════════════════════════════════════════════════════════════
# API
# ══════════════════════════════════════════════════════════════════════════════

def fetch_market_chart(coin_id: str, days: int = 365) -> dict:
    r = requests.get(
        f"{BASE_URL}/coins/{coin_id}/market_chart",
        params={"vs_currency": "usd", "days": days, "interval": "daily"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def fetch_markets_current() -> list:
    r = requests.get(
        f"{BASE_URL}/coins/markets",
        params={
            "vs_currency": "usd",
            "ids": ",".join(c["id"] for c in COINS),
            "order": "market_cap_desc",
            "per_page": 50, "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h,7d",
        },
        timeout=20,
    )
    r.raise_for_status()
    return r.json()


def store_market_chart(coin_id: str, data: dict) -> int:
    prices = data.get("prices", [])
    mcs    = data.get("market_caps", [])
    vols   = data.get("total_volumes", [])
    rows   = [
        (
            coin_id,
            datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d"),
            price,
            mcs[i][1]  if i < len(mcs)  else None,
            vols[i][1] if i < len(vols) else None,
        )
        for i, (ts, price) in enumerate(prices)
    ]
    conn = sqlite3.connect(DB_PATH)
    conn.executemany(
        "INSERT OR REPLACE INTO market_snapshots "
        "(crypto_id, snapshot_date, price_usd, market_cap, total_volume) "
        "VALUES (?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    return len(rows)


def store_current(data: list) -> None:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        (
            c["id"], now,
            c.get("current_price"),    c.get("market_cap"),
            c.get("total_volume"),     c.get("high_24h"),
            c.get("low_24h"),          c.get("price_change_24h"),
            c.get("price_change_percentage_24h"),
            c.get("price_change_percentage_7d_in_currency"),
            c.get("market_cap_rank"),  c.get("circulating_supply"),
            c.get("total_supply"),     c.get("max_supply"),
            c.get("ath"),              c.get("ath_change_percentage"),
        )
        for c in data
    ]
    conn = sqlite3.connect(DB_PATH)
    conn.executemany(
        "INSERT INTO market_current "
        "(crypto_id, collected_at, price_usd, market_cap, total_volume, "
        " high_24h, low_24h, price_change_24h, price_change_percentage_24h, "
        " price_change_percentage_7d, market_cap_rank, circulating_supply, "
        " total_supply, max_supply, ath, ath_change_percentage) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════════════════════

def fmt_pct(x: float) -> str:
    if pd.isna(x):
        return "N/A"
    return f"{'▲' if x > 0 else '▼'} {abs(x):.2f}%"


def build_dashboard_df(df: pd.DataFrame) -> pd.DataFrame:
    """Compute latest prices + 24h/7d/30d % changes from market_snapshots."""
    latest = df.sort_values("snapshot_date").groupby("name", as_index=False).last()
    rows = []
    for name, grp in df.sort_values("snapshot_date").groupby("name"):
        p  = grp["price_usd"].values
        p0 = p[-1]
        rows.append({
            "name":    name,
            "chg_24h": (p0 / p[-2]  - 1) * 100 if len(p) >= 2  else float("nan"),
            "chg_7d":  (p0 / p[-8]  - 1) * 100 if len(p) >= 8  else float("nan"),
            "chg_30d": (p0 / p[-31] - 1) * 100 if len(p) >= 31 else float("nan"),
        })
    df_dash = (
        latest.merge(pd.DataFrame(rows), on="name")
        .sort_values("market_cap", ascending=False)
        .reset_index(drop=True)
    )
    df_dash["rank"] = range(1, len(df_dash) + 1)
    return df_dash


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

def page_overview() -> None:
    st.title("🪙 Cryptocurrency Market Analysis System")
    st.markdown(
        "**Advanced Databases – Final Project** &nbsp;|&nbsp; "
        "Michał Dusza · Szymon Bugajski · Mateusz Basiura"
    )
    st.divider()

    stats = load_db_stats()

    c1, c2, c3 = st.columns(3)
    c1.metric("Tracked Coins",    stats["cryptocurrencies"])
    c2.metric("Daily Snapshots",  f"{stats['market_snapshots']:,}")
    c3.metric("Live Snapshots",   stats["market_current"])

    if stats["date_from"]:
        st.success(
            f"📅 Historical data: **{stats['date_from']}** → **{stats['date_to']}**"
        )
    else:
        st.warning(
            "⚠️ No data yet. Go to **📥 Data Collection** and fetch data from the API."
        )

    st.divider()
    st.subheader("Navigation guide")
    st.markdown("""
| Page | Description |
|------|-------------|
| 📥 **Data Collection** | Fetch / refresh data from CoinGecko API and inspect DB contents |
| 📈 **Time Series** | Line chart: price / market cap / volume over time — 6 interactive filters |
| 📊 **Quantitative Analysis** | Bar / Box / Violin charts — 6 interactive filters |
| 🗺️ **Market Dashboard** | KPI cards · summary table · grouped bar · heatmap · treemap |
| 🔗 **Correlation & Volatility** | Return correlation matrix · annualised volatility · rolling correlation |
""")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DATA COLLECTION
# ══════════════════════════════════════════════════════════════════════════════

def page_data_collection() -> None:
    st.title("📥 Data Collection")
    st.markdown(
        "Fetch and persist cryptocurrency market data from the "
        "[CoinGecko Public API](https://www.coingecko.com/en/api)."
    )

    stats = load_db_stats()
    if stats["date_to"]:
        st.info(
            f"Database already contains **{stats['market_snapshots']:,}** daily records "
            f"({stats['date_from']} → {stats['date_to']}). "
            "Running the fetch again will add any missing days."
        )

    days_opt = st.selectbox(
        "Historical depth",
        [90, 180, 365, 730],
        index=2,
        format_func=lambda x: f"{x} days (~{x//30} months)",
    )

    st.markdown("---")

    col_hist, col_live = st.columns(2)

    # ── Historical data ────────────────────────────────────────────────────────
    with col_hist:
        st.subheader("📅 Historical Data")
        st.caption(f"Endpoint: `GET /coins/{{id}}/market_chart?days={days_opt}`")
        if st.button("🔄 Fetch Historical Data", type="primary", use_container_width=True):
            progress = st.progress(0, text="Initialising…")
            status   = st.empty()
            errors   = []

            for i, coin in enumerate(COINS):
                label = f"[{i+1}/{len(COINS)}] {coin['name']} ({coin['symbol']})"
                progress.progress(i / len(COINS), text=label)
                try:
                    data = fetch_market_chart(coin["id"], days=days_opt)
                    n    = store_market_chart(coin["id"], data)
                    status.success(f"✅ {coin['name']}: {n} records stored")
                except Exception as exc:
                    errors.append(f"{coin['name']}: {exc}")
                    status.error(f"❌ {coin['name']}: {exc}")

                if i < len(COINS) - 1:
                    time.sleep(REQUEST_DELAY)

            progress.progress(1.0, text="Done!")
            if errors:
                st.error("Errors: " + " | ".join(errors))
            else:
                st.success("🎉 All historical data stored!")

            load_snapshots.clear()
            load_db_stats.clear()
            st.rerun()

    # ── Live snapshot ──────────────────────────────────────────────────────────
    with col_live:
        st.subheader("⚡ Live Snapshot")
        st.caption("Endpoint: `GET /coins/markets`")
        st.markdown(
            "Fetches current price, rank, ATH, 24h/7d changes.  \n"
            f"Current live records in DB: **{stats['market_current']}**"
        )
        if st.button("⚡ Fetch Live Snapshot", use_container_width=True):
            with st.spinner("Fetching from API…"):
                try:
                    current_data = fetch_markets_current()
                    store_current(current_data)
                    st.success(
                        f"✅ Stored live snapshot for {len(current_data)} coins"
                    )
                    load_db_stats.clear()
                    st.rerun()
                except Exception as exc:
                    st.error(f"❌ {exc}")

    st.divider()
    st.subheader("📊 Database Contents")

    conn = sqlite3.connect(DB_PATH)
    df_s = pd.read_sql("""
        SELECT c.name, c.symbol,
               COUNT(*)                    AS records,
               MIN(s.snapshot_date)        AS from_date,
               MAX(s.snapshot_date)        AS to_date,
               ROUND(MIN(s.price_usd), 2)  AS min_price_usd,
               ROUND(MAX(s.price_usd), 2)  AS max_price_usd,
               ROUND(AVG(s.price_usd), 2)  AS avg_price_usd
        FROM market_snapshots s
        JOIN cryptocurrencies c ON s.crypto_id = c.id
        GROUP BY c.id
        ORDER BY MAX(s.market_cap) DESC
    """, conn)
    conn.close()

    if not df_s.empty:
        st.dataframe(df_s, use_container_width=True, hide_index=True)
    else:
        st.info("No snapshot data yet.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: TIME SERIES
# ══════════════════════════════════════════════════════════════════════════════

def page_time_series() -> None:
    st.title("📈 Time Series Analysis")

    df = load_snapshots()
    if df.empty:
        st.warning("No data. Go to **📥 Data Collection** first.")
        return

    all_names = sorted(df["name"].unique().tolist())
    date_min  = df["snapshot_date"].min().date()
    date_max  = df["snapshot_date"].max().date()

    # ── Sidebar filters ────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("📈 Filters")

        sel_coins = st.multiselect(
            "1. Cryptocurrencies",
            all_names,
            default=["Bitcoin", "Ethereum"],
        )
        st.markdown("**2–3. Date range**")
        c1, c2 = st.columns(2)
        start_date = c1.date_input(
            "Start", value=date_max - timedelta(days=180),
            min_value=date_min, max_value=date_max, label_visibility="visible",
        )
        end_date = c2.date_input(
            "End", value=date_max,
            min_value=date_min, max_value=date_max, label_visibility="visible",
        )
        metric_label = st.selectbox("4. Metric", list(METRIC_MAP.keys()))
        ma_window    = st.slider("5. Moving Average (days)", 0, 30, 7,
                                  help="0 = raw data; >0 = rolling mean")
        log_scale    = st.checkbox("6. Logarithmic Y-axis")

    if not sel_coins:
        st.warning("Select at least one coin in the sidebar.")
        return

    metric_col = METRIC_MAP[metric_label]

    filtered = df[
        df["name"].isin(sel_coins)
        & (df["snapshot_date"] >= pd.Timestamp(start_date))
        & (df["snapshot_date"] <= pd.Timestamp(end_date))
    ].copy()

    if filtered.empty:
        st.warning("No data for the selected filters.")
        return

    if ma_window > 1:
        filtered = filtered.sort_values(["name", "snapshot_date"])
        filtered[metric_col] = filtered.groupby("name")[metric_col].transform(
            lambda x: x.rolling(ma_window, min_periods=1).mean()
        )
        title_ma = f"  |  {ma_window}-day MA"
    else:
        title_ma = ""

    fig = px.line(
        filtered,
        x="snapshot_date", y=metric_col, color="name",
        title=f"{metric_label} – {', '.join(sel_coins)}{title_ma}",
        labels={"snapshot_date": "Date", metric_col: metric_label, "name": "Coin"},
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig.update_traces(line=dict(width=1.8))
    fig.update_layout(
        height=500,
        hovermode="x unified",
        yaxis_type="log" if log_scale else "linear",
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        margin=dict(l=60, r=20, t=80, b=50),
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📄 Raw data table"):
        st.dataframe(
            filtered.sort_values(["name", "snapshot_date"]),
            use_container_width=True, hide_index=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: QUANTITATIVE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

def page_quantitative() -> None:
    st.title("📊 Quantitative Analysis")

    df = load_snapshots()
    if df.empty:
        st.warning("No data. Go to **📥 Data Collection** first.")
        return

    all_names = sorted(df["name"].unique().tolist())

    with st.sidebar:
        st.header("📊 Filters")
        sel_coins    = st.multiselect("1. Cryptocurrencies", all_names, default=all_names)
        metric_label = st.selectbox("2. Metric", list(METRIC_MAP.keys()), index=1)
        period_label = st.selectbox("3. Time period", list(PERIOD_MAP.keys()), index=2)
        agg_label    = st.selectbox("4. Aggregation", list(AGG_MAP.keys()))
        sort_order   = st.radio("5. Sort order", ["Descending", "Ascending"])
        chart_type   = st.selectbox("6. Chart type", ["Bar Chart", "Box Plot", "Violin Plot"])

    if not sel_coins:
        st.warning("Select at least one coin.")
        return

    metric_col = METRIC_MAP[metric_label]
    days       = PERIOD_MAP[period_label]
    agg_key    = AGG_MAP[agg_label]
    ascending  = sort_order == "Ascending"

    cutoff   = df["snapshot_date"].max() - pd.Timedelta(days=days)
    filtered = df[df["name"].isin(sel_coins) & (df["snapshot_date"] >= cutoff)]

    if filtered.empty:
        st.warning("No data for the selected filters.")
        return

    palette = px.colors.qualitative.Bold

    if chart_type == "Bar Chart":
        agg_df = (
            filtered.groupby("name")[metric_col]
            .agg(agg_key).reset_index()
            .sort_values(metric_col, ascending=ascending)
        )
        fig = px.bar(
            agg_df, x="name", y=metric_col, color="name",
            text_auto=".3s",
            title=f"{agg_label} {metric_label}  |  {period_label}",
            labels={"name": "Coin", metric_col: metric_label},
            template="plotly_dark",
            color_discrete_sequence=palette,
        )
        fig.update_traces(textfont_size=12, textangle=0, textposition="outside")

    elif chart_type == "Box Plot":
        order = (
            filtered.groupby("name")[metric_col].median()
            .sort_values(ascending=ascending).index.tolist()
        )
        fig = px.box(
            filtered, x="name", y=metric_col, color="name",
            category_orders={"name": order},
            title=f"Distribution of {metric_label}  |  {period_label}",
            labels={"name": "Coin", metric_col: metric_label},
            template="plotly_dark",
            color_discrete_sequence=palette,
        )

    else:  # Violin
        order = (
            filtered.groupby("name")[metric_col].median()
            .sort_values(ascending=ascending).index.tolist()
        )
        fig = px.violin(
            filtered, x="name", y=metric_col, color="name",
            box=True, points="outliers",
            category_orders={"name": order},
            title=f"Distribution of {metric_label}  |  {period_label}",
            labels={"name": "Coin", metric_col: metric_label},
            template="plotly_dark",
            color_discrete_sequence=palette,
        )

    fig.update_layout(
        height=480, showlegend=False,
        margin=dict(l=60, r=20, t=80, b=50),
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📄 Aggregated data"):
        if chart_type == "Bar Chart":
            st.dataframe(agg_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(
                filtered.groupby("name")[metric_col].describe(),
                use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MARKET DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def page_market_dashboard() -> None:
    st.title("🗺️ Market Overview Dashboard")

    df = load_snapshots()
    if df.empty:
        st.warning("No data. Go to **📥 Data Collection** first.")
        return

    df_dash = build_dashboard_df(df)

    # ── KPI cards ──────────────────────────────────────────────────────────────
    cols = st.columns(len(df_dash))
    for i, (_, row) in enumerate(df_dash.iterrows()):
        chg = row["chg_24h"]
        cols[i].metric(
            label=f"**{row['symbol']}**",
            value=f"${row['price_usd']:,.2f}",
            delta=f"{chg:+.2f}%" if pd.notna(chg) else "N/A",
        )

    st.divider()

    # ── Summary table ──────────────────────────────────────────────────────────
    st.subheader("📋 Summary Table")
    disp = df_dash[["rank","name","symbol","price_usd","market_cap",
                     "total_volume","chg_24h","chg_7d","chg_30d"]].copy()
    disp.columns = ["#","Coin","Sym","Price (USD)","Market Cap",
                    "Volume 24h","Chg 24h","Chg 7d","Chg 30d"]
    disp["Price (USD)"]  = disp["Price (USD)"].apply(lambda x: f"${x:,.2f}")
    disp["Market Cap"]   = disp["Market Cap"].apply(lambda x: f"${x/1e9:.2f} B")
    disp["Volume 24h"]   = disp["Volume 24h"].apply(lambda x: f"${x/1e9:.2f} B")
    for col in ["Chg 24h", "Chg 7d", "Chg 30d"]:
        disp[col] = disp[col].apply(fmt_pct)
    st.dataframe(disp, use_container_width=True, hide_index=True)

    st.divider()

    # ── Grouped bar: price changes ─────────────────────────────────────────────
    st.subheader("📊 Price Change by Period")
    df_melt = df_dash[["name","chg_24h","chg_7d","chg_30d"]].melt(
        id_vars="name", var_name="period", value_name="pct"
    )
    df_melt["period"] = df_melt["period"].map(
        {"chg_24h": "24h", "chg_7d": "7d", "chg_30d": "30d"}
    )
    fig_bar = px.bar(
        df_melt, x="name", y="pct", color="period",
        barmode="group", text_auto=".2f",
        labels={"name": "Coin", "pct": "Change (%)", "period": "Period"},
        template="plotly_dark",
        color_discrete_map={"24h": "#4ea8de", "7d": "#f4a460", "30d": "#a8e6cf"},
    )
    fig_bar.add_hline(y=0, line_dash="dash", line_color="#444", line_width=1)
    fig_bar.update_layout(
        height=360, yaxis_ticksuffix="%",
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        margin=dict(l=60, r=20, t=40, b=50),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Heatmap + Treemap side by side ─────────────────────────────────────────
    col_heat, col_tree = st.columns(2)

    with col_heat:
        st.subheader("🌡️ Change Heatmap")
        heat_df = (
            df_dash.set_index("name")[["chg_24h", "chg_7d", "chg_30d"]]
            .rename(columns={"chg_24h": "24h %", "chg_7d": "7d %", "chg_30d": "30d %"})
            .T
        )
        fig_heat = px.imshow(
            heat_df, text_auto=".2f",
            color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
            zmin=-20, zmax=20, template="plotly_dark", aspect="auto",
        )
        fig_heat.update_traces(textfont=dict(size=13))
        fig_heat.update_layout(
            height=300, margin=dict(l=70, r=20, t=30, b=20),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_tree:
        st.subheader("🗺️ Market Cap Treemap")
        fig_tree = px.treemap(
            df_dash, path=["name"], values="market_cap",
            color="chg_24h",
            color_continuous_scale="RdYlGn", color_continuous_midpoint=0,
            custom_data=["symbol", "price_usd", "chg_24h"],
            template="plotly_dark",
        )
        fig_tree.update_traces(
            texttemplate=(
                "<b>%{label}</b><br>"
                "$%{customdata[1]:,.0f}<br>"
                "%{customdata[2]:+.2f}%"
            ),
            textfont=dict(size=13),
            marker_line_width=2,
            marker_line_color="#0d0d1a",
        )
        fig_tree.update_layout(
            height=300, margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_tree, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CORRELATION & VOLATILITY
# ══════════════════════════════════════════════════════════════════════════════

def page_correlation() -> None:
    st.title("🔗 Correlation & Volatility Analysis")

    df = load_snapshots()
    if df.empty:
        st.warning("No data. Go to **📥 Data Collection** first.")
        return

    all_names = sorted(df["name"].unique().tolist())

    with st.sidebar:
        st.header("🔗 Filters")
        sel_coins    = st.multiselect("Cryptocurrencies", all_names, default=all_names)
        period_label = st.selectbox("Period", list(PERIOD_MAP.keys()), index=4)

    if len(sel_coins) < 2:
        st.warning("Select at least 2 coins.")
        return

    days     = PERIOD_MAP[period_label]
    cutoff   = df["snapshot_date"].max() - pd.Timedelta(days=days)
    filtered = df[df["name"].isin(sel_coins) & (df["snapshot_date"] >= cutoff)]

    price_pivot = filtered.pivot(
        index="snapshot_date", columns="name", values="price_usd"
    )
    returns = price_pivot.pct_change().dropna()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Correlation Matrix")
        corr     = returns.corr()
        fig_corr = px.imshow(
            corr, text_auto=".2f",
            color_continuous_scale="RdBu_r", color_continuous_midpoint=0,
            zmin=-1, zmax=1, template="plotly_dark",
        )
        fig_corr.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_corr, use_container_width=True)

    with col2:
        st.subheader("Annualised Volatility")
        volatility = (returns.std() * (365 ** 0.5) * 100).reset_index()
        volatility.columns = ["Coin", "Annualised Volatility (%)"]
        volatility = volatility.sort_values("Annualised Volatility (%)", ascending=False)

        fig_vol = px.bar(
            volatility, x="Coin", y="Annualised Volatility (%)",
            color="Coin", text_auto=".1f",
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_vol.update_layout(
            height=400, showlegend=False,
            yaxis_ticksuffix="%",
            margin=dict(l=60, r=20, t=40, b=50),
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    # ── Rolling 30-day correlation with Bitcoin ────────────────────────────────
    if "Bitcoin" in sel_coins and len(sel_coins) > 1:
        st.subheader("Rolling 30-day Correlation with Bitcoin")
        others  = [c for c in sel_coins if c != "Bitcoin"]
        fig_roll = go.Figure()
        for coin in others:
            if coin in returns.columns:
                roll = returns["Bitcoin"].rolling(30).corr(returns[coin])
                fig_roll.add_trace(go.Scatter(
                    x=roll.index, y=roll.values,
                    name=f"BTC / {coin}", mode="lines",
                    line=dict(width=1.8),
                ))
        fig_roll.add_hline(y=0, line_dash="dash", line_color="#444")
        fig_roll.update_layout(
            template="plotly_dark", height=380,
            hovermode="x unified", yaxis_range=[-1, 1],
            yaxis_title="Correlation",
            legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
            margin=dict(l=60, r=20, t=60, b=50),
        )
        st.plotly_chart(fig_roll, use_container_width=True)

    # ── Descriptive stats ──────────────────────────────────────────────────────
    with st.expander("📄 Descriptive statistics of daily returns"):
        st.dataframe(returns.describe().map(lambda x: f"{x:.4f}"),
                     use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    st.set_page_config(
        page_title="Crypto Market Analysis",
        page_icon="🪙",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    create_database()

    pages = {
        "🏠 Overview":                page_overview,
        "📥 Data Collection":         page_data_collection,
        "📈 Time Series":             page_time_series,
        "📊 Quantitative Analysis":   page_quantitative,
        "🗺️ Market Dashboard":        page_market_dashboard,
        "🔗 Correlation & Volatility": page_correlation,
    }

    with st.sidebar:
        st.image(
            "https://static.coingecko.com/s/coingecko-logo-d13d6bcceddbb003f146b33c2f7e8193d72b93bb25d8838e43f7804c31c1f71b.png",
            width=160,
        )
        st.markdown("### Navigation")
        page_name = st.radio(
            "Go to",
            list(pages.keys()),
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("Advanced Databases Project\nMichał Dusza · Szymon Bugajski\nMateusz Basiura")

    pages[page_name]()


if __name__ == "__main__":
    main()
