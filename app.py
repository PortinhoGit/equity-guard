"""
app.py — Equity Guard  v2.0
Premium B3 stock analyzer · Dark mode · i18n PT/EN/ES
Login por e-mail · Créditos · Mercado Pago Pix (UI shell)
"""

import math
import sys
import os
from typing import Optional
from analytics import register_visit, get_stats, get_daily_series
from market_status import get_status_mercado, dia_util_anterior

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from config import (
    ADMIN_EMAIL, ANON_QUERY_LIMIT, USER_QUERY_LIMIT, DEMO_TICKER,
    APP_NAME, APP_ICON, APP_VERSION,
    SELIC_RATE, SELIC_NEXT_MEETING, FED_FUNDS_RATE, FED_NEXT_MEETING,
    PREVDOW_DATA, NITRO_DATA,
)
from i18n import get_translator, TRANSLATIONS, SUPPORTED_LANGS
from auth.manager import (
    get_or_create_user, load_user, use_credit, has_credits, get_all_users,
    get_favorites, add_favorite, remove_favorite, get_history, add_history,
)
from ui.payment import render_payment_page
from data.tickers_b3 import ALL_TICKERS_B3
from data.provider import (
    get_full_data,
    normalize_ticker,
    get_price_performance,
    get_dividend_calendar,
    get_dividend_month_pattern,
    detect_dividend_frequency,
    get_stock_history,
    get_fx_usdbrl,
    get_global_indicators,
)
from core.valuation import (
    calculate_avg_dividends,
    calculate_teto_barsi,
    calculate_safety_margin,
    check_health_indicators,
    generate_buy_signal,
    identify_best_sector,
    project_dividends,
)
from core.technical import (
    calculate_rsi,
    calculate_moving_averages,
    detect_tops_bottoms,
    get_current_rsi,
    analyze_trend,
)

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Equity Guard — Terminal Financeiro · B3",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

_OG_IMAGE_URL = "https://raw.githubusercontent.com/PortinhoGit/equity-guard/main/assets/og-image.png"
st.markdown(
    f"""<head>
    <meta property="og:title" content="Equity Guard — Terminal Financeiro"/>
    <meta property="og:description" content="Análise técnica e fundamentalista de ações da B3 e indicadores macroeconômicos."/>
    <meta property="og:image" content="{_OG_IMAGE_URL}"/>
    <meta property="og:url" content="https://equityguard.streamlit.app/"/>
    <meta property="og:type" content="website"/>
    <meta name="twitter:card" content="summary_large_image"/>
    <meta name="twitter:title" content="Equity Guard — Terminal Financeiro"/>
    <meta name="twitter:description" content="Análise técnica e fundamentalista de ações da B3 e indicadores macroeconômicos."/>
    <meta name="twitter:image" content="{_OG_IMAGE_URL}"/>
    </head>
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-BBKMK9TL6P"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-BBKMK9TL6P');
    </script>""",
    unsafe_allow_html=True,
)

# ─── CSS Premium Dark Mode ────────────────────────────────────────────────────

_CSS = """
html, body, [data-testid="stApp"] {
    background-color: #0d1117 !important;
    color: #e6edf3;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #21262d !important;
}
[data-testid="stSidebar"] * { color: #e6edf3 !important; }
[data-testid="stSidebar"] hr { border-color: #30363d !important; }
div[data-testid="metric-container"] {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    transition: border-color .25s, box-shadow .25s;
}
div[data-testid="metric-container"]:hover {
    border-color: #d4af37 !important;
    box-shadow: 0 0 14px rgba(212,175,55,.15);
}
div[data-testid="metric-container"] label { color: #8b949e !important; font-size:.82rem !important; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e6edf3 !important; font-weight:700 !important;
}
.stButton > button {
    background: #161b22 !important; color: #d4af37 !important;
    border: 1px solid #30363d !important; border-radius: 8px !important;
    font-weight: 600 !important; transition: all .2s !important;
}
.stButton > button:hover {
    border-color: #d4af37 !important;
    box-shadow: 0 0 12px rgba(212,175,55,.25) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#b8941f,#d4af37) !important;
    color: #0d1117 !important; border: none !important;
    font-weight: 800 !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg,#d4af37,#f0d060) !important;
    box-shadow: 0 0 20px rgba(212,175,55,.45) !important;
    transform: translateY(-1px);
}
.stTextInput > div > div > input {
    background-color: #0d1117 !important; color: #e6edf3 !important;
    border: 1px solid #30363d !important; border-radius: 8px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #d4af37 !important;
    box-shadow: 0 0 0 2px rgba(212,175,55,.2) !important;
}
.stTextInput label, .stSelectbox label, .stSlider label { color: #8b949e !important; font-size:.82rem !important; }
.stSelectbox > div > div { background-color: #0d1117 !important; border-color: #30363d !important; color: #e6edf3 !important; }
hr { border-color: #21262d !important; margin: 1rem 0 !important; }
h1, h2, h3, h4 { color: #e6edf3 !important; }
.stDataFrame { border: 1px solid #30363d !important; border-radius: 10px !important; overflow: hidden; }
.stCaption, small { color: #6e7681 !important; }
/* Login */
.eg-login-hero { text-align:center; padding:3.5rem 2rem 2rem; }
.eg-logo-wordmark { font-size:3.2rem; font-weight:900; letter-spacing:-2px; line-height:1; }
.eg-logo-gold { color:#d4af37; }
.eg-logo-white { color:#e6edf3; }
.eg-tagline { color:#8b949e; font-size:.88rem; letter-spacing:1.5px; text-transform:uppercase; margin-top:.5rem; }
.eg-login-features { display:flex; justify-content:center; gap:16px; margin:1.2rem 0; flex-wrap:wrap; }
.eg-feature-pill { background:#161b22; border:1px solid #30363d; border-radius:20px; padding:4px 12px; font-size:.76rem; color:#8b949e; }
.eg-login-footer { text-align:center; color:#6e7681; font-size:.74rem; margin-top:1.5rem; line-height:1.8; }
/* Credit badge */
.eg-credit-badge { background:#0d1117; border:1px solid #d4af37; border-radius:20px; padding:6px 14px; font-size:.82rem; color:#d4af37; text-align:center; margin:8px 0; }
/* Signal */
.eg-signal { border-radius:12px; padding:13px 18px; text-align:center; font-size:1.05rem; font-weight:800; letter-spacing:.5px; border:1px solid rgba(255,255,255,.08); }
/* Nav menu */
.eg-nav-menu {
    background: #1c2333; border: 1px solid #d4af37;
    border-radius: 12px; padding: 8px 12px; display: flex; gap: 4px;
    overflow-x: auto; -webkit-overflow-scrolling: touch;
    scrollbar-width: none; justify-content: center;
    margin-bottom: 12px; flex-wrap: wrap;
}
.eg-nav-menu::-webkit-scrollbar { display: none; }
.eg-nav-btn {
    background: rgba(212,175,55,0.06); color: #e6edf3;
    border: 1px solid #30363d; border-radius: 20px;
    padding: 6px 14px; font-size: 0.78rem; font-weight: 600;
    white-space: nowrap; cursor: pointer;
    transition: all 0.2s; font-family: 'Inter', system-ui, sans-serif;
}
.eg-nav-btn:hover {
    color: #0d1117; border-color: #d4af37;
    background: #d4af37;
}
.eg-nav-topo { color: #d4af37; border-color: #d4af37; margin-left: auto; }
/* Health row */
.eg-health-row { display:flex; justify-content:space-between; align-items:center; padding:9px 14px; border-radius:8px; margin:5px 0; font-size:.88rem; border:1px solid #30363d; }
/* Best badge */
.eg-best-badge { display:inline-block; background:rgba(212,175,55,.12); border:1px solid #d4af37; color:#d4af37; padding:2px 12px; border-radius:20px; font-size:.76rem; font-weight:700; letter-spacing:.5px; vertical-align:middle; margin-left:8px; }
/* Dev badge */
.eg-dev-badge { display:inline-block; background:rgba(212,175,55,.10); border:1px dashed #d4af37; color:#d4af37; padding:2px 10px; border-radius:20px; font-size:.72rem; font-weight:700; letter-spacing:.5px; vertical-align:middle; margin-left:8px; }
/* Beta badge + aviso */
.eg-beta-badge { display:inline-block; background:linear-gradient(135deg,#f85149,#d4af37); color:#0d1117; font-size:.66rem; font-weight:900; letter-spacing:1.6px; padding:3px 10px; border-radius:20px; margin-left:10px; vertical-align:middle; animation:eg-beta-pulse 2.2s infinite; }
@keyframes eg-beta-pulse { 0%,100% { box-shadow:0 0 0 0 rgba(248,81,73,.55); } 50% { box-shadow:0 0 0 6px rgba(248,81,73,0); } }
.eg-beta-notice { background:rgba(248,81,73,.08); border:1px dashed #f85149; border-radius:8px; padding:7px 14px; color:#ffffff; font-size:.76rem; text-align:center; margin:8px 0 10px; }
/* Feedback box */
.eg-fb-wrap { background:#161b22; border:1px solid #30363d; border-radius:12px; padding:14px 16px; margin:14px 0; }
.eg-fb-title { font-size:.82rem; font-weight:800; letter-spacing:.8px; color:#d4af37; text-transform:uppercase; margin-bottom:4px; }
.eg-fb-sub { font-size:.72rem; color:#8b949e; margin-bottom:10px; }
.eg-fb-btns { display:flex; gap:8px; flex-wrap:wrap; margin-top:8px; }
.eg-fb-btn { padding:7px 14px; border-radius:8px; text-decoration:none !important; font-weight:700; font-size:.78rem; letter-spacing:.3px; display:inline-flex; align-items:center; gap:6px; transition:transform .15s, box-shadow .2s; }
.eg-fb-btn:hover { transform:translateY(-1px); box-shadow:0 4px 14px rgba(0,0,0,.3); }
.eg-fb-wa { background:#25d366; color:#0d1117 !important; }
.eg-fb-mail { background:#d4af37; color:#0d1117 !important; }
.eg-fb-btn-off { opacity:.45; pointer-events:none; }
/* Section header */
.eg-section-header { font-size:.72rem; font-weight:700; letter-spacing:1.8px; text-transform:uppercase; color:#8b949e; margin:1.2rem 0 .6rem; }
/* Ticker chip — aparece antes de cada seção para identificar a ação analisada */
.eg-ticker-chip {
    display:inline-flex; align-items:center; gap:8px;
    background:#0d1117; border:1px solid #30363d; border-left:3px solid #d4af37;
    border-radius:6px; padding:5px 12px;
    font-size:.72rem; font-weight:700; color:#e6edf3;
    letter-spacing:.2px; margin:14px 0 8px;
    font-family:'Inter',system-ui,sans-serif;
}
.eg-ticker-chip-sym {
    color:#d4af37;
    font-family:'SF Mono','Consolas','Monaco',monospace;
    font-size:.7rem; font-weight:800;
    padding:2px 7px; border-radius:4px;
    background:rgba(212,175,55,.08);
}
/* Trend */
.eg-trend-box { border-radius:10px; padding:12px; text-align:center; font-weight:700; font-size:1rem; margin-bottom:12px; border:1px solid rgba(255,255,255,.06); }
/* MA row */
.eg-ma-row { display:flex; justify-content:space-between; padding:7px 12px; background:#161b22; border:1px solid #21262d; border-radius:7px; margin:4px 0; font-size:.88rem; }
/* RSI gauge */
.eg-rsi-track { background:#21262d; border-radius:20px; height:10px; margin:7px 0 4px; overflow:hidden; }
.eg-rsi-fill { height:100%; border-radius:20px; transition:width .6s ease; }
.eg-rsi-labels { display:flex; justify-content:space-between; font-size:.68rem; color:#6e7681; }
/* Margin bars */
.eg-margin-ok { background:rgba(63,185,80,.1); border:1px solid rgba(63,185,80,.3); padding:10px 16px; border-radius:8px; margin-top:8px; font-size:.88rem; }
.eg-margin-risk { background:rgba(248,81,73,.1); border:1px solid rgba(248,81,73,.3); padding:10px 16px; border-radius:8px; margin-top:8px; font-size:.88rem; }
/* Disclaimer */
.eg-disclaimer { background:rgba(139,148,158,.06); border:1px solid #21262d; border-radius:8px; padding:10px 16px; font-size:.76rem; color:#8b949e; text-align:center; margin-top:1rem; }
/* ── Mobile / PWA responsive tweaks ─────────────────────────────────────── */
@media (max-width: 768px) {
    /* Tighter padding so cards don't overflow */
    [data-testid="stAppViewContainer"] > .main .block-container {
        padding-left: .6rem !important;
        padding-right: .6rem !important;
        padding-top: .8rem !important;
    }
    /* Headers a bit smaller to save vertical space */
    h1 { font-size: 1.4rem !important; }
    h3 { font-size: 1.05rem !important; }
    /* Metric cards shrink cleanly */
    div[data-testid="metric-container"] {
        padding: 10px 12px !important;
    }
    /* Horizontal scroll for wide dataframes instead of overflow */
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch;
    }
    /* Plotly charts: limit height on mobile */
    [data-testid="stPlotlyChart"] > div { max-height: 380px !important; }
    /* Let plotly charts breathe */
    [data-testid="stPlotlyChart"] { overflow: hidden; }
    /* Top auth bar: stack buttons full-width on mobile */
    [data-testid="stHorizontalBlock"] [data-testid="column"] .stButton > button {
        font-size: .82rem !important;
    }
}
/* All widths: ensure tables never break layout horizontally */
[data-testid="stDataFrame"] > div { overflow-x: auto !important; }
/* mobile balloon placeholder — rendered via st.components.v1.html */
/* ── Z-index defensivo: radios/headers acima do container Plotly ─────────── */
[data-testid="stRadio"], .eg-section-header {
    position: relative !important;
    z-index: 10 !important;
}
[data-testid="stPlotlyChart"] { position: relative; z-index: 1; }
/* ── Plotly modebar: flip tooltip above button (prevents covering chart) ── */
.js-plotly-plot .modebar-btn { position: relative !important; }
.js-plotly-plot .modebar-btn::before,
.js-plotly-plot .modebar-btn::after,
.js-plotly-plot .modebar-btn[data-title]:hover::before,
.js-plotly-plot .modebar-btn[data-title]:hover::after {
    top: auto !important;
    bottom: calc(100% + 6px) !important;
    transform: translateX(-50%) !important;
}
.js-plotly-plot .modebar-btn[data-title]:hover::after {
    border-top: 4px solid rgba(0,0,0,.85) !important;
    border-bottom: none !important;
}
.js-plotly-plot .modebar-container { top: 18px !important; }
"""


# ── PWA meta tags — injected ONCE at the top of every run ─────────────────────
_PWA_META = """
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5, viewport-fit=cover">
<meta name="theme-color" content="#0d1117">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Equity Guard">
<meta name="mobile-web-app-capable" content="yes">
<meta name="application-name" content="Equity Guard">
<link rel="apple-touch-icon" href="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%230d1117'/><text x='50' y='68' font-size='60' text-anchor='middle' fill='%23d4af37'>⚡</text></svg>">
"""


def _inject_css() -> None:
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)
    st.markdown(_PWA_META, unsafe_allow_html=True)


# ─── Currency helper ──────────────────────────────────────────────────────────

_CURRENCY_SYMBOLS = {
    "USD": "US$",
    "GBP": "£",
    "EUR": "€",
    "BRL": "R$",
    "JPY": "¥",
    "CHF": "CHF",
    "CAD": "C$",
    "AUD": "A$",
    "HKD": "HK$",
    "CNY": "¥",
}

def _currency_symbol(code: str) -> str:
    """Returns the display symbol for an ISO currency code (USD→$, BRL→R$ …)."""
    code = (code or "BRL").upper()
    return _CURRENCY_SYMBOLS.get(code, code)


def _fmt_money(value: float, cs: str) -> str:
    """
    Locale-aware money formatting with the symbol attached (no space).
        BRL: R$1.234,56          (period thousands · comma decimal)
        USD: $1,234.56           (comma thousands · period decimal)
        GBP/EUR: same as USD
    """
    if cs == "R$":
        s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        s = f"{value:,.2f}"
    return f"{cs}{s}"


def _fmt_int(value: int, cs: str) -> str:
    """Locale-aware integer formatting (no symbol). BRL uses '.' thousands; others use ','."""
    if cs == "R$":
        return f"{value:,}".replace(",", ".")
    return f"{value:,}"


def _md_to_html(s: str) -> str:
    """
    Converts **bold** markdown to <b>bold</b> HTML so it renders correctly
    inside an unsafe_allow_html container (where markdown is NOT processed).
    """
    import re as _re
    return _re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)


# ─── Plotly dark theme defaults ───────────────────────────────────────────────

_CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e6edf3", size=12),
    margin=dict(l=10, r=10, t=36, b=10),
    legend=dict(
        bgcolor="rgba(22,27,34,.9)", bordercolor="#30363d", borderwidth=1,
        font=dict(color="#e6edf3", size=11),
        orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
    ),
)
_AXIS = dict(gridcolor="rgba(255,255,255,.05)", zeroline=False, linecolor="#30363d", tickfont=dict(color="#8b949e"))


# ─── Chart builders ───────────────────────────────────────────────────────────

def _main_chart(df: pd.DataFrame, teto: float, ticker: str, T: dict, cs: str = "R$") -> go.Figure:
    df_ma = calculate_moving_averages(df)
    rsi_s = calculate_rsi(df_ma)
    current = float(df_ma["Close"].iloc[-1])

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[.72, .28], vertical_spacing=.04,
        subplot_titles=(T["chart_title"], "RSI (14)"),
    )
    fig.add_trace(go.Candlestick(
        x=df_ma.index, open=df_ma["Open"], high=df_ma["High"],
        low=df_ma["Low"], close=df_ma["Close"], name="Price",
        increasing=dict(line=dict(color="#58a6ff"), fillcolor="#58a6ff"),
        decreasing=dict(line=dict(color="#dc2626"), fillcolor="#dc2626"),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df_ma.index, y=df_ma["MA20"], name="MA20 (Curta)",
        line=dict(color="#e3b341", width=1.6),
        hovertemplate=f"MA20: {cs} %{{y:.2f}}<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df_ma.index, y=df_ma["MA200"], name="MA200 (Longa)",
        line=dict(color="#bc8cff", width=2.0),
        hovertemplate=f"MA200: {cs} %{{y:.2f}}<extra></extra>",
    ), row=1, col=1)

    if teto > 0:
        below = current <= teto
        fill_c = "rgba(63,185,80,.10)" if below else "rgba(248,81,73,.10)"
        line_c = "rgba(63,185,80,.85)" if below else "rgba(248,81,73,.85)"
        x_vals = list(df_ma.index) + list(reversed(df_ma.index))
        y_vals = [teto * 1.08] * len(df_ma) + [teto * .92] * len(df_ma)
        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals, fill="toself", fillcolor=fill_c,
            line=dict(color="rgba(0,0,0,0)"),
            name=T["zone_legend"], hoverinfo="skip",
        ), row=1, col=1)
        fig.add_hline(
            y=teto, line_dash="dash", line_color=line_c, line_width=1.8,
            annotation_text=f"  {teto:.2f}",
            annotation_font=dict(color=line_c, size=11),
            annotation_position="top right", row=1, col=1,
        )

    try:
        tops, bottoms = detect_tops_bottoms(df_ma, window=8)
        if not tops.empty:
            fig.add_trace(go.Scatter(
                x=tops.index, y=tops.values, mode="markers", name=T["top_marker"],
                marker=dict(color="#dc2626", size=7, symbol="triangle-down"),
                hovertemplate=f"{T['top_marker']}: {cs} %{{y:.2f}}<extra></extra>",
            ), row=1, col=1)
        if not bottoms.empty:
            fig.add_trace(go.Scatter(
                x=bottoms.index, y=bottoms.values, mode="markers", name=T["bottom_marker"],
                marker=dict(color="#58a6ff", size=7, symbol="triangle-up"),
                hovertemplate=f"{T['bottom_marker']}: {cs} %{{y:.2f}}<extra></extra>",
            ), row=1, col=1)
    except Exception:
        pass

    if rsi_s is not None and not rsi_s.dropna().empty:
        fig.add_trace(go.Scatter(
            x=df_ma.index, y=rsi_s, name="RSI",
            line=dict(color="#58a6ff", width=1.6),
            hovertemplate="RSI: %{y:.1f}<extra></extra>",
        ), row=2, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(248,81,73,.07)", line_width=0, row=2, col=1)
        fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(63,185,80,.07)",  line_width=0, row=2, col=1)
        for lvl, col in [(70, "rgba(248,81,73,.5)"), (30, "rgba(63,185,80,.5)"), (50, "rgba(139,148,158,.3)")]:
            fig.add_hline(y=lvl, line_dash="dot", line_color=col, line_width=1, row=2, col=1)

    fig.update_layout(height=500, hovermode="x unified", xaxis_rangeslider_visible=False, **_CHART_LAYOUT)
    for ax in ["xaxis", "xaxis2", "yaxis", "yaxis2"]:
        fig.update_layout(**{ax: _AXIS})
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    for ann in fig.layout.annotations:
        ann.font = dict(color="#8b949e", size=11)
    return fig


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_full_data(ticker: str, period: str):
    """Cached wrapper for get_full_data (5-min TTL)."""
    return get_full_data(ticker, period=period)


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_prevdow_live() -> dict:
    """
    Scraper PrevDow com cache 1h. Retorna dict merged com PREVDOW_DATA.
    Se scraper falhar, retorna PREVDOW_DATA do config.
    """
    try:
        from data.prevdow_scraper import get_rentabilidade_prevdow
        live = get_rentabilidade_prevdow()
    except Exception:
        live = None
    merged = dict(PREVDOW_DATA)
    if live:
        if live.get("data_base"):
            merged["data_base"] = live["data_base"]
        if live.get("cdi_month") is not None:
            merged["cdi_month"] = live["cdi_month"]
        if live.get("balanced_month") is not None:
            merged["balanced_month"] = live["balanced_month"]
    return merged


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_quick_history(ticker: str, period: str) -> Optional[pd.DataFrame]:
    """Cached wrapper for the interactive period chart (5-min TTL)."""
    return get_stock_history(ticker, period)


@st.cache_data(ttl=120, show_spinner=False)
def _fetch_intraday(ticker: str, interval: str, period: str) -> Optional[pd.DataFrame]:
    """
    Fetch intraday OHLC+Volume. TTL curto (2 min) porque intraday muda rapido.
    yfinance limits:
      - 5m: periodo max 60 dias
      - 15m/30m: 60 dias
      - 1h: 730 dias
    """
    import yfinance as yf
    ticker_sa = normalize_ticker(ticker)
    try:
        tk = yf.Ticker(ticker_sa)
        df = tk.history(period=period, interval=interval, auto_adjust=True)
        if df is None or df.empty:
            return None
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_convert("America/Sao_Paulo").tz_localize(None)
        return df
    except Exception:
        return None


def _intraday_chart(df: pd.DataFrame, T: dict, cs: str, interval_label: str) -> "go.Figure":
    """
    Grafico intraday estilo TradingView: candles + MM9/MM21 (medias curtas,
    padrao intraday) + subplot de volume. Sem Preco Teto Barsi, sem Zona
    de Valor, sem MM longa — esses sao referenciais de longo prazo.
    """
    df_i = df.copy()
    df_i["MM9"] = df_i["Close"].rolling(9).mean()
    df_i["MM21"] = df_i["Close"].rolling(21).mean()
    # Labels locale-aware (MM em PT/ES, MA em EN)
    _mm_prefix = "MM" if T.get("ma_short", "MA20").startswith("MM") else "MA"

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[.76, .24], vertical_spacing=.03,
        subplot_titles=(f"{T['chart_title']} · {interval_label}", "Volume"),
    )
    fig.add_trace(go.Candlestick(
        x=df_i.index, open=df_i["Open"], high=df_i["High"],
        low=df_i["Low"], close=df_i["Close"], name="Price",
        increasing=dict(line=dict(color="#58a6ff"), fillcolor="#58a6ff"),
        decreasing=dict(line=dict(color="#dc2626"), fillcolor="#dc2626"),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df_i.index, y=df_i["MM9"], name=f"{_mm_prefix}9",
        line=dict(color="#e3b341", width=1.4),
        hovertemplate=f"{_mm_prefix}9: {cs} %{{y:.2f}}<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df_i.index, y=df_i["MM21"], name=f"{_mm_prefix}21",
        line=dict(color="#bc8cff", width=1.6),
        hovertemplate=f"{_mm_prefix}21: {cs} %{{y:.2f}}<extra></extra>",
    ), row=1, col=1)

    if "Volume" in df_i.columns:
        _vcolors = [
            "#58a6ff" if c >= o else "#dc2626"
            for o, c in zip(df_i["Open"], df_i["Close"])
        ]
        fig.add_trace(go.Bar(
            x=df_i.index, y=df_i["Volume"], name="Volume",
            marker=dict(color=_vcolors, line=dict(width=0)),
            hovertemplate="Volume: %{y:,.0f}<extra></extra>",
        ), row=2, col=1)

    fig.update_layout(
        height=560, margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(color="#e6edf3", family="Inter, system-ui, sans-serif"),
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        showlegend=True,
    )
    # rangebreaks: esconde fins de semana + horas fora de pregao B3 (10h-18h BRT).
    # Assim candles ficam concentrados nas sessoes reais, sem espacos mortos.
    fig.update_xaxes(
        gridcolor="#21262d", zerolinecolor="#21262d",
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
            dict(bounds=[18, 10], pattern="hour"),
        ],
    )
    fig.update_yaxes(gridcolor="#21262d", zerolinecolor="#21262d")
    return fig


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_fx_usdbrl() -> Optional[dict]:
    """Cached wrapper for the USDBRL macro panel (10-min TTL)."""
    return get_fx_usdbrl()


def _render_share_buttons(T: dict) -> None:
    """Social share buttons with correct share URLs + email + copy."""
    import urllib.parse as _url
    _share_url = "https://equityguard.streamlit.app/"
    _raw_url = _share_url
    _app_url = _url.quote(_share_url)
    _title = _url.quote(T["share_title"])
    _body = _url.quote(T["share_body"].format(url=_raw_url))

    _btn_style = (
        "display:inline-flex;align-items:center;justify-content:center;"
        "width:32px;height:32px;border-radius:50%;"
        "color:#fff;font-size:.78rem;font-weight:800;text-decoration:none;"
        "cursor:pointer;transition:transform .2s,box-shadow .2s;"
        "border:1px solid #30363d;"
    )

    _icons = [
        ("WhatsApp", "#25d366", f"https://wa.me/?text={_title}%20{_app_url}", "W"),
        ("Facebook", "#1877f2", f"https://www.facebook.com/sharer/sharer.php?u={_app_url}", "f"),
        ("X", "#1d1d1d", f"https://twitter.com/intent/tweet?url={_app_url}&text={_title}", "𝕏"),
        ("LinkedIn", "#0a66c2", f"https://www.linkedin.com/sharing/share-offsite/?url={_app_url}", "in"),
        ("Telegram", "#0088cc", f"https://t.me/share/url?url={_app_url}&text={_title}", "✈"),
        ("TikTok", "#010101", f"https://www.tiktok.com/", "♪"),
        ("E-mail", "#8b949e", f"mailto:?subject={_title}&body={_body}", "✉"),
        ("Truth Social", "#5448ee", f"https://truthsocial.com/share?url={_app_url}&title={_title}", "T"),
    ]

    btns = ""
    for name, color, url, icon in _icons:
        _tip = T["share_tooltip"].format(name=name)
        btns += (
            f"<a href='{url}' target='_blank' title='{_tip}' style='"
            f"{_btn_style}background:{color};' "
            f"onmouseover=\"this.style.transform='scale(1.15)';this.style.boxShadow='0 0 10px {color}80'\" "
            f"onmouseout=\"this.style.transform='scale(1)';this.style.boxShadow='none'\">"
            f"{icon}</a>"
        )

    btns += (
        f"<button title='Copiar link' onclick=\"navigator.clipboard.writeText('{_raw_url}');"
        f"this.innerText='✓';setTimeout(()=>this.innerText='📋',1500)\" style='"
        f"{_btn_style}background:#30363d;'>"
        f"📋</button>"
    )

    st.markdown(
        f"<div style='display:flex;gap:8px;justify-content:center;flex-wrap:wrap;"
        f"padding:6px 0;'>{btns}</div>",
        unsafe_allow_html=True,
    )


_FEEDBACK_TO = ["portinho@icloud.com", "vhmonje@gmail.com"]


def _send_feedback_email(msg_text: str) -> tuple[bool, str]:
    """Envia feedback via SMTP. Credenciais em st.secrets. Fallback: mailto: (retorna False)."""
    import smtplib
    from email.mime.text import MIMEText
    from email.utils import formatdate

    try:
        _secrets = st.secrets
        smtp_host = _secrets.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(_secrets.get("SMTP_PORT", 587))
        smtp_user = _secrets.get("SMTP_USER")
        smtp_pass = _secrets.get("SMTP_PASS")
        smtp_from = _secrets.get("SMTP_FROM", smtp_user)
    except Exception:
        return False, "SMTP não configurado nos secrets."

    if not smtp_user or not smtp_pass:
        return False, "SMTP não configurado (SMTP_USER/SMTP_PASS)."

    body = f"{msg_text}\n\n— enviado via https://equityguard.streamlit.app"
    mime = MIMEText(body, "plain", "utf-8")
    mime["Subject"] = "[Equity Guard] Feedback do usuário"
    mime["From"] = smtp_from
    mime["To"] = ", ".join(_FEEDBACK_TO)
    mime["Date"] = formatdate(localtime=True)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, _FEEDBACK_TO, mime.as_string())
        return True, "ok"
    except Exception as e:
        return False, f"Falha SMTP: {e}"


def _render_feedback_box() -> None:
    """Caixa de feedback: 1 botão envia e-mail via SMTP para os mantenedores.

    Se SMTP não estiver configurado nos secrets, cai num fallback mailto: que
    abre o cliente de e-mail do usuário com ambos destinatários já preenchidos.
    """
    import urllib.parse as _url

    st.markdown(
        "<div class='eg-fb-wrap'>"
        "<div class='eg-fb-title'>💬 Caixa de feedback</div>"
        "<div class='eg-fb-sub'>Versão beta — envie sugestões, elogios ou reporte problemas. "
        "Sua mensagem <b>não é publicada</b> no site. Um clique envia e-mail para os mantenedores.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    with st.form(key="eg_feedback_form", clear_on_submit=True):
        _msg = st.text_area(
            "Sua mensagem",
            key="eg_feedback_msg",
            placeholder="Ex.: achei a análise de BBAS3 muito útil, mas faltou o histórico de JCP…",
            height=110,
            label_visibility="collapsed",
        )
        _clicked = st.form_submit_button("📨 Enviar feedback", use_container_width=False)

    if _clicked:
        _msg_clean = (_msg or "").strip()
        if not _msg_clean:
            st.warning("Digite uma mensagem antes de enviar.")
            return
        with st.spinner("Enviando…"):
            ok, detail = _send_feedback_email(_msg_clean)
        if ok:
            st.success("✓ Feedback enviado! Obrigado.")
        else:
            _subject = _url.quote("[Equity Guard] Feedback do usuário")
            _body = _url.quote(f"{_msg_clean}\n\n— enviado via https://equityguard.streamlit.app")
            _mailto = f"mailto:{','.join(_FEEDBACK_TO)}?subject={_subject}&body={_body}"
            st.warning(
                "Envio automático indisponível no momento. "
                f"[Clique aqui para abrir seu e-mail com a mensagem pronta]({_mailto})."
            )
            st.caption(f"_Detalhe técnico: {detail}_")


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_global_indicators() -> list:
    """Cached wrapper for the global indicators bar (5-min TTL)."""
    return get_global_indicators()




def _fmt_index_value(val: float, locale: str) -> str:
    """Format index / commodity values with locale-aware thousands separator."""
    if val is None:
        return "—"
    if locale == "br":
        # IBOVESPA — BR style: 132.456  (no decimals, integer thousands)
        return f"{int(round(val)):,}".replace(",", ".")
    # US style: 5,234.56
    return f"{val:,.2f}"


def _maybe_pension_alert(T: dict) -> None:
    """
    After the 15th, shows a clickable banner that opens the sidebar (pension).
    Resets when PREVDOW_DATA["data_base"] changes.
    """
    today = pd.Timestamp.now()
    if today.day < 15:
        return
    ref      = PREVDOW_DATA.get("data_base", "")
    seen_key = f"_pension_seen_{ref}"
    if not ref or st.session_state.get(seen_key):
        return

    import streamlit.components.v1 as _comp
    _msg = T["pension_alert_toast"].format(ref=ref)
    _comp.html(f"""
    <script>
    (function() {{
        var doc = window.parent.document;
        if (doc.getElementById('eg-pension-alert')) return;
        var bar = doc.createElement('div');
        bar.id = 'eg-pension-alert';
        bar.innerHTML = '🏦 {_msg} — <u>ver agora</u> ✕';
        bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:999998;'
            + 'background:linear-gradient(135deg,#c0392b,#e74c3c);color:#fff;'
            + 'padding:8px 60px 8px 16px;font-size:12px;font-weight:700;text-align:center;'
            + 'cursor:pointer;font-family:Inter,system-ui,sans-serif;';
        bar.onclick = function() {{
            var openBtn = doc.querySelector('[data-testid="collapsedControl"]');
            if (openBtn) openBtn.click();
            var delay = openBtn ? 600 : 50;
            setTimeout(function() {{
                var sidebar = doc.querySelector('[data-testid="stSidebar"]');
                if (!sidebar) return;
                var anchor = sidebar.querySelector('#sidebar-prevdow');
                if (anchor) {{
                    anchor.scrollIntoView({{behavior:'smooth', block:'start'}});
                }} else {{
                    var inner = sidebar.querySelector('[data-testid="stSidebarContent"]')
                             || sidebar.querySelector('section[data-testid="stSidebar"] > div');
                    if (inner) inner.scrollTo({{top: inner.scrollHeight * 0.4, behavior:'smooth'}});
                }}
            }}, delay);
            bar.remove();
        }};
        doc.body.appendChild(bar);
        setTimeout(function() {{ if (bar.parentNode) bar.remove(); }}, 15000);
    }})();
    </script>
    """, height=0)
    st.session_state[seen_key] = True


def _render_briefing(T: dict) -> None:
    """
    🗞️ Briefing de Fechamento — layout em duas colunas: Bolsas e Commodities.
    """
    import urllib.parse as _url

    inds = _fetch_global_indicators()
    by_name = {i["name"]: i for i in inds}

    def _fmt_val(ind_name: str, locale_hint: str = "us") -> str:
        ind = by_name.get(ind_name)
        if not ind or ind.get("last") is None:
            return "—"
        return _fmt_index_value(ind["last"], locale_hint)

    def _fmt_chg(ind_name: str) -> str:
        ind = by_name.get(ind_name)
        if not ind:
            return ""
        chg = ind.get("change") or 0
        arrow = "▲" if chg > 0 else ("▼" if chg < 0 else "■")
        color = "#58a6ff" if chg > 0 else ("#dc2626" if chg < 0 else "#8b949e")
        return f"<span style='color:{color};font-weight:700;'>{arrow}{chg:+.2f}%</span>"

    def _chg_trio(ind_name: str) -> str:
        """Retorna 'dia | YTD | 1A' formatado para o card."""
        ind = by_name.get(ind_name)
        if not ind:
            return ""
        def _c(v):
            if v is None:
                return "<span style='color:#484f58;'>—</span>"
            c = "#58a6ff" if v > 0 else ("#dc2626" if v < 0 else "#8b949e")
            return f"<span style='color:{c};font-weight:700;'>{v:+.1f}%</span>"
        chg = ind.get("change") or 0
        ytd = ind.get("chg_ytd")
        y1 = ind.get("chg_1y")
        return (
            f"<div style='display:flex;gap:6px;justify-content:flex-end;font-size:.68rem;margin-top:2px;'>"
            f"<span style='color:#484f58;'>dia</span>{_c(chg)} "
            f"<span style='color:#484f58;'>YTD</span>{_c(ytd)} "
            f"<span style='color:#484f58;'>1A</span>{_c(y1)}</div>"
        )

    def _wa_chg_trio(ind_name: str) -> str:
        """Retorna 'dia/YTD/1A' para WhatsApp texto."""
        ind = by_name.get(ind_name)
        if not ind:
            return ""
        chg = ind.get("change") or 0
        ytd = ind.get("chg_ytd")
        y1 = ind.get("chg_1y")
        ytd_s = f"{ytd:+.1f}%" if ytd is not None else "—"
        y1_s = f"{y1:+.1f}%" if y1 is not None else "—"
        return f"dia {chg:+.1f}% · YTD {ytd_s} · 1A {y1_s}"

    def _fmt_date_br(iso: str) -> str:
        try:
            return pd.Timestamp(iso).strftime("%d/%m/%Y")
        except Exception:
            return iso

    def _card(name: str, val: str, chg_html: str) -> str:
        return (
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"padding:6px 0;border-bottom:1px solid #21262d;'>"
            f"<span style='color:#8b949e;font-size:.82rem;'>{name}</span>"
            f"<span style='font-size:.88rem;'>"
            f"<b style='color:#e6edf3;'>{val}</b> {chg_html}</span></div>"
        )

    today = pd.Timestamp.now(tz="America/Sao_Paulo").strftime("%d/%m/%Y")
    with st.expander(T["briefing_title"].format(date=today), expanded=True):

        _bc1, _bc2 = st.columns(2)

        with _bc1:
            brent_val = _fmt_val("Brent")
            wti_val = _fmt_val("WTI")
            _aa = T.get("rate_annual", "a.a.")
            _fed_label = f"🇺🇸 Fed Funds · FOMC {_fmt_date_br(FED_NEXT_MEETING)}"
            _selic_label = f"🇧🇷 Selic · COPOM {_fmt_date_br(SELIC_NEXT_MEETING)}"
            st.markdown(
                f"<div style='background:#161b22;border:1px solid #30363d;"
                f"border-radius:10px;padding:14px 16px;'>"
                f"<div style='font-size:.78rem;color:#d4af37;font-weight:700;"
                f"text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;'>"
                f"{T['briefing_juros']}</div>"
                f"{_card(_fed_label, f'{FED_FUNDS_RATE:.2f}% {_aa}', '')}"
                f"{_card(_selic_label, f'{SELIC_RATE:.2f}% {_aa}', '')}"
                f"<div style='height:8px;'></div>"
                f"<div style='font-size:.78rem;color:#d4af37;font-weight:700;"
                f"text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;'>"
                f"{T['briefing_commodities_label']}</div>"
                f"{_card('Brent', f'US$ {brent_val}', _chg_trio('Brent'))}"
                f"{_card('WTI', f'US$ {wti_val}', _chg_trio('WTI'))}"
                f"<div style='font-size:.55rem;color:#484f58;text-align:right;margin-top:8px;'>"
                f"{T['briefing_source_left']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        with _bc2:
            st.markdown(
                f"<div style='background:#161b22;border:1px solid #30363d;"
                f"border-radius:10px;padding:14px 16px;'>"
                f"<div style='font-size:.78rem;color:#d4af37;font-weight:700;"
                f"text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;'>"
                f"{T['briefing_bolsas']}</div>"
                f"{_card('Ibovespa', _fmt_val('IBOV', 'br'), _chg_trio('IBOV'))}"
                f"{_card('S&P 500', _fmt_val('S&P 500'), _chg_trio('S&P 500'))}"
                f"{_card('NASDAQ', _fmt_val('NASDAQ'), _chg_trio('NASDAQ'))}"
                f"{_card('FTSE', _fmt_val('FTSE'), _chg_trio('FTSE'))}"
                f"<div style='font-size:.55rem;color:#484f58;text-align:right;margin-top:8px;'>"
                f"{T['briefing_source_right']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # ── WhatsApp share — botões conforme status do mercado ────────────────
        _mkt = get_status_mercado()
        _fx_wa = _fetch_fx_usdbrl()
        _pd = _fetch_prevdow_live()
        # NitroPrev (IFM) suspenso no briefing — conteudo de portal privado.
        import streamlit.components.v1 as _wa_comp

        def _fx_fmt_wa(v):
            return f"R${v:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".") if v else "---"

        def _wa_chg(name):
            ind = by_name.get(name)
            if not ind or ind.get("change") is None:
                return ""
            c = ind["change"]
            arrow = "+" if c > 0 else ""
            return f"{arrow}{c:.1f}%"

        def _wa_val(name, loc="us"):
            return _fmt_val(name, loc)

        _now_brt = pd.Timestamp.now(tz="America/Sao_Paulo")
        _hora_online = _now_brt.strftime("%H:%M:%S")
        _data_ref = _mkt["data_ref"].strftime("%d/%m/%Y")
        _data_ant = _mkt["data_anterior"].strftime("%d/%m/%Y")
        _is_online = _mkt["estado"] == "ONLINE"

        _fx_com = _fx_fmt_wa(_fx_wa.get("com_ask")) if _fx_wa else "---"
        _fx_prev = _fx_fmt_wa(_fx_wa.get("com_prev")) if _fx_wa else "---"
        _fx_chg_val = (_fx_wa or {}).get("change", 0)
        _fx_arrow = "+" if _fx_chg_val > 0 else ""
        _hora_corte = _mkt["hora_corte"].strftime("%Hh%M")

        def _pad(name, width=10):
            return name + " " * max(1, width - len(name))

        def _rpad(val, width=12):
            return " " * max(1, width - len(val)) + val

        _emoji_js = """
            msg = msg.replace('*Juros*', String.fromCodePoint(0x1F3E6)+' *Juros*');
            msg = msg.replace('US Fed:', String.fromCodePoint(0x1F1FA,0x1F1F8)+' Fed:');
            msg = msg.replace('BR Selic:', String.fromCodePoint(0x1F1E7,0x1F1F7)+' Selic:');
            msg = msg.replace('*Commodities*', String.fromCodePoint(0x1F6E2)+' *Commodities*');
            msg = msg.replace('*Dolar Comercial*', String.fromCodePoint(0x1F4B5)+' *Dolar Comercial*');
            msg = msg.replace('*Bolsas*', String.fromCodePoint(0x1F4C8)+' *Bolsas*');
            msg = msg.replace('*Prevdow', String.fromCodePoint(0x1F3E6)+' *Prevdow');
            msg = msg.replace('*NitroPrev', String.fromCodePoint(0x1F3E6)+' *NitroPrev');
            msg = msg.replace('*Briefing', String.fromCodePoint(0x1F4CA)+' *Briefing');
            msg = msg.replace('*Equity Guard*', String.fromCodePoint(0x1F449)+' *Equity Guard*');
        """

        # Formato: nome: valor variacao (sem tentativa de alinhar colunas — WhatsApp usa fonte proporcional)
        _juros_block = (
            "*Juros*\\n"
            + "US Fed: " + f"{FED_FUNDS_RATE:.2f}%" + " (FOMC " + _fmt_date_br(FED_NEXT_MEETING) + ")\\n"
            + "BR Selic: " + f"{SELIC_RATE:.2f}%" + " (COPOM " + _fmt_date_br(SELIC_NEXT_MEETING) + ")"
        )
        def _fmt_pct(v):
            return f"{v:+.2f}%" if v is not None else "N/D"
        _prev_di = _fmt_pct(_pd.get('cdi_month'))
        _prev_bal = _fmt_pct(_pd.get('balanced_month'))
        _prev_di_y = _fmt_pct(_pd.get('cdi_year'))
        _prev_bal_y = _fmt_pct(_pd.get('balanced_year'))
        _prev_block = (
            "*Prevdow " + _pd['data_base'] + "*\\n"
            + "DI: " + _prev_di + " mes | " + _prev_di_y + " ano\\n"
            + "Balanceada: " + _prev_bal + " mes | " + _prev_bal_y + " ano"
        )
        _footer = "_Cortesia YlvorixVHM_\\n*Equity Guard*\\nhttps://equityguard.streamlit.app"

        _body_block = (
            _juros_block + "\\n\\n"
            + "*Commodities*\\n"
            + "Brent: US$ " + _wa_val('Brent') + "  " + _wa_chg('Brent') + "\\n"
            + "WTI: US$ " + _wa_val('WTI') + "  " + _wa_chg('WTI') + "\\n\\n"
            + "*Dolar Comercial*\\n"
            + "Venda: " + _fx_com + "  " + _fx_arrow + f"{_fx_chg_val:+.1f}%" + "\\n\\n"
            + "*Bolsas*\\n"
            + "Ibovespa: " + _wa_val('IBOV', 'br') + "  " + _wa_chg('IBOV') + "\\n"
            + "S&P 500: " + _wa_val('S&P 500') + "  " + _wa_chg('S&P 500') + "\\n"
            + "NASDAQ: " + _wa_val('NASDAQ') + "  " + _wa_chg('NASDAQ') + "\\n"
            + "FTSE: " + _wa_val('FTSE') + "  " + _wa_chg('FTSE') + "\\n\\n"
            + _prev_block + "\\n\\n"
            + _footer
        )

        # ── Fechamento do último pregão (data_ref) ───────────────────────────
        _close_msg = (
            "*Briefing Equity Guard*\\n"
            + "*Fechamento " + _data_ref + ", " + _hora_corte + ".*\\n\\n"
            + _body_block
        )

        # ── Fechamento anterior (data_anterior) ──────────────────────────────
        _ant_msg = (
            "*Briefing Equity Guard*\\n"
            + "*Fechamento " + _data_ant + ", " + _hora_corte + ".*\\n\\n"
            + _body_block
        )

        # ── Online (só quando mercado aberto) ────────────────────────────────
        _online_msg = (
            "*Briefing Equity Guard*\\n"
            + "*Online " + today + " " + _hora_online + " (Brasilia)*\\n\\n"
            + _body_block
        )

        if _is_online:
            # Mercado aberto: vermelho (fechamento anterior) + verde (online)
            _wa_comp.html("""
            <div style="display:flex;flex-direction:column;gap:6px;">
            <button onclick="
                var msg = '""" + _ant_msg + """';
                """ + _emoji_js + """
                window.parent.open('https://wa.me/?text=' + encodeURIComponent(msg), '_blank');
            " style="
                display:block;width:100%;background:#c0392b;color:#fff;
                padding:10px 8px;border-radius:8px;font-size:.78rem;
                font-weight:700;border:none;cursor:pointer;
                font-family:Inter,system-ui,sans-serif;
            ">Fechamento """ + _data_ant + """</button>
            <button onclick="
                var msg = '""" + _online_msg + """';
                """ + _emoji_js + """
                window.parent.open('https://wa.me/?text=' + encodeURIComponent(msg), '_blank');
            " style="
                display:block;width:100%;background:#25d366;color:#fff;
                padding:10px 8px;border-radius:8px;font-size:.78rem;
                font-weight:700;border:none;cursor:pointer;
                font-family:Inter,system-ui,sans-serif;
            ">Online """ + _hora_online + """ (Brasilia)</button>
            </div>
            """, height=90)
        else:
            # Mercado fechado: vermelho (fechamento de hoje) + cinza (anterior)
            _wa_comp.html("""
            <div style="display:flex;flex-direction:column;gap:6px;">
            <button onclick="
                var msg = '""" + _close_msg + """';
                """ + _emoji_js + """
                window.parent.open('https://wa.me/?text=' + encodeURIComponent(msg), '_blank');
            " style="
                display:block;width:100%;background:#c0392b;color:#fff;
                padding:10px 8px;border-radius:8px;font-size:.78rem;
                font-weight:700;border:none;cursor:pointer;
                font-family:Inter,system-ui,sans-serif;
            ">Fechamento """ + _data_ref + """ (""" + _hora_corte + """)</button>
            <button onclick="
                var msg = '""" + _ant_msg + """';
                """ + _emoji_js + """
                window.parent.open('https://wa.me/?text=' + encodeURIComponent(msg), '_blank');
            " style="
                display:block;width:100%;background:#484f58;color:#e6edf3;
                padding:10px 8px;border-radius:8px;font-size:.78rem;
                font-weight:700;border:none;cursor:pointer;
                font-family:Inter,system-ui,sans-serif;
            ">Fechamento anterior """ + _data_ant + """</button>
            </div>
            """, height=90)
        st.markdown(
            f"<div style='font-size:.58rem;color:#484f58;text-align:right;margin-top:4px;'>"
            f"{T['briefing_source_footer']}</div>",
            unsafe_allow_html=True,
        )

        # ── Enviar para meu WhatsApp ─────────────────────────────────────────
        st.markdown(
            "<div style='margin-top:12px;border-top:1px solid #21262d;padding-top:10px;'>"
            "<div style='font-size:.72rem;color:#d4af37;font-weight:700;"
            "text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;'>"
            "📲 Enviar briefing para meu WhatsApp</div></div>",
            unsafe_allow_html=True,
        )
        # Formulario HTML/JS puro — nao depende de rerender Streamlit,
        # nao sofre popup blocker (window.open vem do click direto do usuario),
        # e permite type="tel"/autocomplete="off" (Streamlit nao expoe).
        import json as _json
        _plain_msg = (
            _online_msg
            .replace("\\n", "\n")
            .replace("\\u00e2", "â").replace("\\u00e1", "á")
            .replace("\\u00e9", "é").replace("\\u00e7", "ç")
            .replace("\\u00e3", "ã").replace("\\u00ea", "ê")
            .replace("\\u00ed", "í").replace("\\u00f3", "ó")
            .replace("\\u00f4", "ô").replace("\\u00f5", "õ")
            .replace("\\u00fa", "ú").replace("\\u00fc", "ü")
        )
        # Emojis sao injetados no JS via String.fromCodePoint — isso sobrevive
        # melhor ao forward do WhatsApp Desktop do que emojis nativos em Python
        # (que podem virar "?" apos re-encoding do cliente desktop).
        _msg_js = _json.dumps(_plain_msg)
        _wa_comp.html(f"""
        <style>
        .eg-wa-wrap {{ display:flex; gap:10px; font-family:Inter,system-ui,sans-serif; }}
        .eg-wa-phone {{
            flex:3; padding:9px 14px; border-radius:8px;
            background:#0d1117; color:#e6edf3; font-size:.88rem;
            border:1px solid #30363d; outline:none;
            font-family:Inter,system-ui,sans-serif;
        }}
        .eg-wa-phone:focus {{ border-color:#d4af37; box-shadow:0 0 0 2px rgba(212,175,55,.15); }}
        .eg-wa-btn {{
            flex:2; padding:9px 14px; border-radius:8px;
            font-size:.82rem; font-weight:700; letter-spacing:.3px;
            cursor:pointer; transition:all .15s;
            display:flex; align-items:center; justify-content:center; gap:6px;
            font-family:Inter,system-ui,sans-serif;
        }}
        .eg-wa-btn.eg-wa-ready {{
            background:#25d366; color:#0d1117; border:1px solid #1cbf5a;
        }}
        .eg-wa-btn.eg-wa-ready:hover {{ filter:brightness(1.08); transform:translateY(-1px); }}
        .eg-wa-btn.eg-wa-off {{
            background:#161b22; color:#6e7681; border:1px solid #30363d;
            cursor:not-allowed;
        }}
        .eg-wa-err {{ color:#f85149; font-size:.72rem; margin-top:6px; min-height:16px; }}
        </style>
        <div class="eg-wa-wrap">
            <input type="tel" inputmode="tel" autocomplete="off"
                   name="eg-wa-phone-anon" id="eg-wa-phone"
                   class="eg-wa-phone" placeholder="Ex.: 11 99999-9999 (BR) ou +1 415 555 2671">
            <button id="eg-wa-send" class="eg-wa-btn eg-wa-off" disabled>Digite seu numero</button>
        </div>
        <div id="eg-wa-err" class="eg-wa-err"></div>
        <script>
        (function() {{
            var msg = {_msg_js};
            var inp = document.getElementById('eg-wa-phone');
            var btn = document.getElementById('eg-wa-send');
            var err = document.getElementById('eg-wa-err');

            function cleanDigits(v) {{ return (v || '').replace(/\\D/g, ''); }}
            function hasPlus(v) {{ return /^\\s*\\+/.test(v || ''); }}
            // 8 a 15 digitos cobrem todos os paises (ITU-T E.164).
            function isValid(d) {{ return d.length >= 8 && d.length <= 15; }}

            function normalize(raw) {{
                var d = cleanDigits(raw);
                if (hasPlus(raw)) return d;          // usuario informou DDI
                if (d.length >= 12) return d;         // provavel DDI ja incluso
                return '55' + d;                      // default Brasil
            }}

            function update() {{
                var d = cleanDigits(inp.value);
                if (isValid(d)) {{
                    btn.disabled = false;
                    btn.className = 'eg-wa-btn eg-wa-ready';
                    btn.textContent = 'Enviar para mim →';
                    err.textContent = '';
                }} else {{
                    btn.disabled = true;
                    btn.className = 'eg-wa-btn eg-wa-off';
                    btn.textContent = 'Digite seu numero';
                }}
            }}
            inp.addEventListener('input', update);
            btn.addEventListener('click', function() {{
                var d = cleanDigits(inp.value);
                if (!isValid(d)) {{
                    err.textContent = 'Numero invalido. Digite DDD + numero ou +DDI numero.';
                    return;
                }}
                d = normalize(inp.value);
                // Detecta mobile. Em computador (Desktop/Windows/Mac), WhatsApp
                // costuma corromper emojis 4-byte no forward, entao enviamos sem.
                var ua = (navigator.userAgent || '') + ' ' + (navigator.platform || '');
                var isMobile = /iPhone|iPad|iPod|Android|Mobile|IEMobile|Opera Mini/i.test(ua);
                var m = msg;
                if (isMobile) {{
                    // Injeta emojis via String.fromCodePoint — preserva UTF-8 correto na URL.
                    m = m.replace('*Briefing Equity Guard*', String.fromCodePoint(0x1F4CA) + ' *Briefing Equity Guard*');
                    m = m.replace('*Juros*', String.fromCodePoint(0x1F3E6) + ' *Juros*');
                    m = m.replace('US Fed:', String.fromCodePoint(0x1F1FA, 0x1F1F8) + ' Fed:');
                    m = m.replace('BR Selic:', String.fromCodePoint(0x1F1E7, 0x1F1F7) + ' Selic:');
                    m = m.replace('*Commodities*', String.fromCodePoint(0x1F6E2) + ' *Commodities*');
                    m = m.replace('*Dolar Comercial*', String.fromCodePoint(0x1F4B5) + ' *Dolar Comercial*');
                    m = m.replace('*Bolsas*', String.fromCodePoint(0x1F4C8) + ' *Bolsas*');
                    m = m.replace('*Prevdow', String.fromCodePoint(0x1F3E6) + ' *Prevdow');
                    m = m.replace('*Equity Guard*', String.fromCodePoint(0x1F449) + ' *Equity Guard*');
                }}
                // Em desktop nao substituimos: mensagem fica com markdown puro
                // (WhatsApp ainda renderiza *negrito* normalmente).
                var url = 'https://wa.me/' + d + '?text=' + encodeURIComponent(m);
                window.open(url, '_blank', 'noopener');
            }});
            update();
        }})();
        </script>
        """, height=100)


def _render_global_bar(T: dict) -> None:
    """
    Top ribbon showing major indices + commodities + central bank rates.
    Renders a 6-card row with IBOV, S&P, NASDAQ, FTSE, Brent, WTI and a
    compact SELIC / Fed rates strip below.
    """
    indicators = _fetch_global_indicators()
    st.markdown(
        f'<div class="eg-section-header" style="margin-top:4px;">{T["global_title"]}</div>',
        unsafe_allow_html=True,
    )

    if not indicators:
        st.caption(T["global_no_data"])
    else:
        cols = st.columns(len(indicators))
        for col, ind in zip(cols, indicators):
            last  = ind.get("last")
            chg   = ind.get("change")
            name  = ind["name"]
            if last is None:
                with col:
                    st.markdown(
                        f"<div style='background:#161b22;border:1px solid #21262d;"
                        f"border-radius:8px;padding:9px 8px;text-align:center;'>"
                        f"<div style='font-size:.68rem;color:#6e7681;'>{name}</div>"
                        f"<div style='font-size:.82rem;color:#6e7681;margin-top:4px;'>—</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                continue
            val_str = _fmt_index_value(last, ind.get("locale", "us"))
            arrow   = "▲" if chg > 0 else ("▼" if chg < 0 else "■")
            color   = "#58a6ff" if chg > 0 else ("#dc2626" if chg < 0 else "#8b949e")
            with col:
                st.markdown(
                    f"<div style='background:#161b22;border:1px solid #21262d;"
                    f"border-radius:8px;padding:9px 8px;text-align:center;'>"
                    f"<div style='font-size:.68rem;color:#6e7681;margin-bottom:3px;'>{name}</div>"
                    f"<div style='font-size:.86rem;font-weight:700;color:#e6edf3;'>{val_str}</div>"
                    f"<div style='font-size:.72rem;font-weight:700;color:{color};margin-top:2px;'>"
                    f"{arrow} {chg:+.2f}%</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # ── Central bank rates strip ──────────────────────────────────────────────
    def _fmt_date(iso: str) -> str:
        try:
            return pd.Timestamp(iso).strftime("%d/%m/%Y")
        except Exception:
            return iso

    st.markdown(
        f"<div style='background:#0d1117;border:1px solid #21262d;"
        f"border-radius:8px;padding:8px 14px;margin-top:8px;"
        f"font-size:.76rem;color:#8b949e;display:flex;"
        f"justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;'>"
        f"<span>🇺🇸 <b style='color:#58a6ff;'>Fed {FED_FUNDS_RATE:.2f}%</b> · "
        f"{T['global_next_meeting']}: <b style='color:#e6edf3;'>{_fmt_date(FED_NEXT_MEETING)}</b></span>"
        f"<span>🇧🇷 <b style='color:#58a6ff;'>SELIC {SELIC_RATE:.2f}%</b> · "
        f"{T['global_next_meeting']}: <b style='color:#e6edf3;'>{_fmt_date(SELIC_NEXT_MEETING)}</b></span>"
        f"<span style='color:#6e7681;font-size:.7rem;'>{T['global_source']}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_prevdow_panel(T: dict) -> None:
    """
    Prevdow — Previdência Complementar.
    Tenta scraper live; fallback para config.PREVDOW_DATA.
    """
    d = _fetch_prevdow_live()

    # ── Branded header (red bar, white text) ──────────────────────────────────
    st.markdown(
        "<div style='background:linear-gradient(135deg,#c0392b,#e74c3c);"
        "border-radius:10px 10px 0 0;padding:10px 14px;margin-top:14px;"
        "border:1px solid #c0392b;border-bottom:none;'>"
        "<div style='display:flex;align-items:center;justify-content:space-between;'>"
        f"<span style='font-size:.88rem;font-weight:800;color:#fff;"
        f"letter-spacing:.3px;'>{T['prevdow_title']}</span>"
        "<span style='font-size:.68rem;color:rgba(255,255,255,.85);'>"
        f"{T['prevdow_subtitle'].format(ref=d['data_base'])}</span>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    # ── Returns table (Perfil | No mês | No ano) ──────────────────────────────
    def _val_html(v) -> str:
        if v is None:
            return "<span style='font-weight:800;color:#6e7681;'>N/D</span>"
        c = "#58a6ff" if v > 0 else ("#dc2626" if v < 0 else "#8b949e")
        return f"<span style='font-weight:800;color:{c};'>{v:+.2f}%</span>"

    _hdr = "color:#6e7681;font-size:.68rem;font-weight:600;text-transform:uppercase;letter-spacing:.3px;"
    _cell = "padding:6px 0;font-size:.82rem;"
    st.markdown(
        "<div style='background:#161b22;border:1px solid #c0392b;"
        "border-top:none;border-radius:0 0 10px 10px;padding:8px 14px 10px;'>"
        "<table style='width:100%;border-collapse:collapse;'>"
        f"<tr style='border-bottom:1px solid #30363d;'>"
        f"<td style='{_hdr}padding-bottom:6px;'>{T['prevdow_profile_col']}</td>"
        f"<td style='{_hdr}padding-bottom:6px;text-align:right;'>{T['prevdow_month']}</td>"
        f"<td style='{_hdr}padding-bottom:6px;text-align:right;'>{T['prevdow_year']}</td>"
        f"</tr>"
        f"<tr style='border-bottom:1px dashed #21262d;'>"
        f"<td style='{_cell}color:#e6edf3;font-weight:600;'>{T['prevdow_cdi_label']}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d.get('cdi_month'))}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d.get('cdi_year'))}</td>"
        f"</tr>"
        f"<tr>"
        f"<td style='{_cell}color:#e6edf3;font-weight:600;'>{T['prevdow_balanced_label']}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d.get('balanced_month'))}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d.get('balanced_year'))}</td>"
        f"</tr>"
        "</table></div>",
        unsafe_allow_html=True,
    )

    # ── Login button ──────────────────────────────────────────────────────────
    st.markdown(
        f"<a href='{d['url']}' target='_blank' style='display:block;"
        f"text-align:center;background:#c0392b;color:#fff;"
        f"padding:10px 8px;border-radius:8px;font-size:.78rem;"
        f"font-weight:800;text-decoration:none;margin-top:6px;"
        f"border:1px solid #e74c3c;letter-spacing:.3px;'>"
        f"{T['prevdow_access']}</a>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div style='font-size:.58rem;color:#484f58;text-align:right;margin-top:2px;'>"
        f"{T['prevdow_source']}</div>",
        unsafe_allow_html=True,
    )


def _render_nitro_panel(T: dict) -> None:
    """
    Nitro Prev (IFM Previdência / Votorantim).
    Apenas link de acesso ao portal oficial. Divulgacao dos indices
    suspensa ate termos autorizacao formal do IFM.
    """
    url = NITRO_DATA.get("url", "https://ifmprev.participante.com.br/login")
    NAVY = "#003366"
    NAVY_HI = "#004488"
    GOLD = "#FFCC00"
    st.markdown(
        f"<div style='background:linear-gradient(135deg,{NAVY},{NAVY_HI});"
        f"border-radius:10px;padding:10px 14px;margin-top:14px;"
        f"border:1px solid {NAVY};'>"
        f"<div style='font-size:.88rem;font-weight:800;color:{GOLD};"
        f"letter-spacing:.3px;margin-bottom:8px;'>{T['nitro_title']}</div>"
        f"<a href='{url}' target='_blank' style='display:block;"
        f"text-align:center;background:{NAVY};color:{GOLD};"
        f"padding:9px 8px;border-radius:6px;font-size:.78rem;"
        f"font-weight:800;text-decoration:none;"
        f"border:1px solid {GOLD};letter-spacing:.3px;'>"
        f"{T['nitro_link']}</a>"
        "</div>",
        unsafe_allow_html=True,
    )


def _render_macro_panel(T: dict) -> None:
    """
    Tiny FX panel (USD/BRL) with a sparkline — rendered inside the sidebar.
    Uses the pre-formatted R$ symbol explicitly because this is Brazilian FX.
    """
    fx = _fetch_fx_usdbrl()
    st.markdown(
        f'<div class="eg-section-header">{T["macro_panel_title"]}</div>',
        unsafe_allow_html=True,
    )
    if not fx:
        st.caption(T["macro_unavailable"])
        return

    com_ask = fx.get("com_ask") or fx.get("ask") or fx.get("last", 0)
    com_bid = fx.get("com_bid") or fx.get("bid") or round(com_ask * 0.995, 4)
    com_prev = fx.get("com_prev") or fx.get("prev", com_ask)
    tur_ask = fx.get("tur_ask") or round(com_ask * 1.04, 4)
    tur_bid = fx.get("tur_bid") or round(com_bid * 1.04, 4)
    tur_prev = fx.get("tur_prev") or round(com_prev * 1.04, 4)
    change = fx.get("change", 0)
    series = fx.get("series")
    fetched = fx.get("fetched_at")

    def _fx(v):
        return f"R${v:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")

    arrow = "▲" if change > 0 else ("▼" if change < 0 else "■")
    color = "#58a6ff" if change > 0 else ("#dc2626" if change < 0 else "#8b949e")

    ts_html = ""
    if fetched is not None:
        _ts = T["macro_updated_at"].format(
            date=fetched.strftime("%d/%m"),
            time=fetched.strftime("%H:%M"),
        )
        ts_html = f"<div style='font-size:.62rem;color:#6e7681;margin-top:6px;'>🕒 {_ts}</div>"

    _hdr = "color:#6e7681;font-size:.62rem;font-weight:600;text-transform:uppercase;letter-spacing:.3px;padding-bottom:4px;"
    _cell = "padding:3px 0;font-size:.82rem;text-align:right;"
    _lbl = "padding:3px 0;font-size:.72rem;color:#8b949e;"
    _gold_cell = "padding:3px 0;font-size:.88rem;text-align:right;font-weight:800;color:#d4af37;"
    _t_com = T.get("fx_commercial", "Comercial")
    _t_tur = T.get("fx_tourism", "Turismo")
    # Label dinamico: ultimo dia util anterior a hoje (ignora fins de semana
    # e feriados B3). Ex.: se hoje = segunda, aponta sexta; se hoje = terca apos
    # feriado, aponta sexta anterior.
    _today_brt = pd.Timestamp.now(tz="America/Sao_Paulo").date()
    _prev_bday = dia_util_anterior(_today_brt)
    _t_prev = T.get("fx_prev_close", "Fech. {date}").format(
        date=_prev_bday.strftime("%d/%m")
    )
    _fx_ytd = fx.get("chg_ytd")
    _fx_1y = fx.get("chg_1y")
    _ytd_str = f"{_fx_ytd:+.1f}%" if _fx_ytd is not None else "—"
    _y1_str = f"{_fx_1y:+.1f}%" if _fx_1y is not None else "—"
    _ytd_color = "#58a6ff" if _fx_ytd and _fx_ytd > 0 else ("#dc2626" if _fx_ytd and _fx_ytd < 0 else "#8b949e")
    _y1_color = "#58a6ff" if _fx_1y and _fx_1y > 0 else ("#dc2626" if _fx_1y and _fx_1y < 0 else "#8b949e")
    _t_online = T.get("fx_online", "Cotação online")
    _t_sell = T.get("fx_sell", "Venda")
    _t_buy = T.get("fx_buy", "Compra")
    _t_chart = T.get("fx_chart_label", "Dólar Comercial (venda) · 7 dias")
    _t_src = T.get("fx_source", "Fonte: BCB PTAX · Yahoo Finance")

    st.markdown(
        f"<div style='background:#161b22;border:1px solid #21262d;"
        f"border-radius:10px;padding:10px 10px 6px;margin-top:2px;'>"
        f"<div style='font-size:.7rem;color:#6e7681;margin-bottom:6px;'>"
        f"{T.get('macro_usdbrl_label', 'Dólar (USD/BRL)')}</div>"
        f"<table style='width:100%;border-collapse:collapse;'>"
        f"<tr style='border-bottom:1px solid #30363d;'>"
        f"<td style='{_hdr}'></td>"
        f"<td style='{_hdr}text-align:right;'>{_t_com}</td>"
        f"<td style='{_hdr}text-align:right;'>{_t_tur}</td></tr>"
        f"<tr style='border-bottom:1px solid #21262d;'>"
        f"<td style='{_lbl}'>{_t_prev}</td>"
        f"<td style='{_cell}color:#6e7681;'>{_fx(com_prev)}</td>"
        f"<td style='{_cell}color:#6e7681;'>{_fx(tur_prev)}</td></tr>"
        f"<tr style='border-bottom:1px solid #21262d;background:rgba(212,175,55,.04);'>"
        f"<td style='{_lbl}color:#d4af37;font-weight:700;'>{_t_online}</td>"
        f"<td style='{_gold_cell}'>{_fx(com_ask)}</td>"
        f"<td style='{_gold_cell}'>{_fx(tur_ask)}</td></tr>"
        f"<tr style='border-bottom:1px solid #21262d;'>"
        f"<td style='{_lbl}'>{_t_sell}</td>"
        f"<td style='{_cell}color:#e6edf3;font-weight:700;'>{_fx(com_ask)}</td>"
        f"<td style='{_cell}color:#e6edf3;font-weight:700;'>{_fx(tur_ask)}</td></tr>"
        f"<tr>"
        f"<td style='{_lbl}'>{_t_buy}</td>"
        f"<td style='{_cell}color:#e6edf3;font-weight:700;'>{_fx(com_bid)}</td>"
        f"<td style='{_cell}color:#e6edf3;font-weight:700;'>{_fx(tur_bid)}</td></tr>"
        f"</table>"
        f"<div style='display:flex;gap:8px;justify-content:flex-end;font-size:.68rem;margin-top:6px;flex-wrap:wrap;'>"
        f"<span><span style='color:#484f58;'>dia</span> <span style='color:{color};font-weight:700;'>{change:+.1f}%</span></span>"
        f"<span><span style='color:#484f58;'>YTD</span> <span style='font-weight:700;color:{_ytd_color};'>{_ytd_str}</span></span>"
        f"<span><span style='color:#484f58;'>1A</span> <span style='font-weight:700;color:{_y1_color};'>{_y1_str}</span></span>"
        f"</div>"
        f"{ts_html}</div>",
        unsafe_allow_html=True,
    )

    # Gráfico dólar comercial venda (7 dias)
    if series is not None and len(series) >= 2:
        st.caption(_t_chart)
        _y_min = float(series.min())
        _y_max = float(series.max())
        _pad = (_y_max - _y_min) * 0.3 if _y_max > _y_min else 0.02
        _fig_fx = go.Figure()
        _fig_fx.add_trace(go.Scatter(
            x=[d.strftime("%d/%m") for d in series.index],
            y=list(series.values),
            mode="lines+markers",
            line=dict(color="#d4af37", width=2),
            marker=dict(size=4, color="#d4af37"),
            fill="tozeroy",
            fillcolor="rgba(212,175,55,.08)",
            hovertemplate="R$ %{y:.4f}<extra></extra>",
        ))
        _fig_fx.update_layout(
            height=120,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            xaxis=dict(showgrid=False, tickfont=dict(color="#6e7681", size=9)),
            yaxis=dict(
                range=[_y_min - _pad, _y_max + _pad],
                showgrid=True, gridcolor="#21262d",
                tickfont=dict(color="#6e7681", size=9),
                tickformat=".4f",
            ),
            hovermode="x unified",
        )
        st.plotly_chart(_fig_fx, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        f"<div style='font-size:.55rem;color:#484f58;text-align:right;margin-top:2px;'>"
        f"{_t_src}</div>",
        unsafe_allow_html=True,
    )


@st.fragment
def _render_interactive_quote(ticker: str, df: pd.DataFrame, T: dict, cs: str) -> None:
    """
    Interactive Quote block (period selector + area chart + OHLC cards).
    Wrapped in @st.fragment so clicking a period button only reruns THIS block,
    not the entire page — keeps scroll position and other state stable.
    """
    st.markdown(
        f'<div class="eg-section-header">{T["chart_quick_title"]}</div>',
        unsafe_allow_html=True,
    )

    _period_keys = ["1d", "5d", "1mo", "6mo", "1y", "5y", "ytd"]
    _period_lbls = [T["period_btn"][k] for k in _period_keys]
    _qp_idx = st.radio(
        "quick_chart_period_radio",
        options=list(range(len(_period_keys))),
        format_func=lambda i: _period_lbls[i],
        horizontal=True,
        index=4,  # default 1A/1Y
        label_visibility="collapsed",
        key="quick_chart_period",
    )
    _chosen_period = _period_keys[_qp_idx]

    _qdf = _fetch_quick_history(normalize_ticker(ticker), _chosen_period)
    if _qdf is not None and not _qdf.empty:
        st.plotly_chart(
            _quick_chart(_qdf, T, cs=cs),
            use_container_width=True,
            config={"displayModeBar": False, "displaylogo": False},
        )
    else:
        st.info(T["chart_no_data"])

    # ── OHLC + 52w summary (always from latest daily data) ────────────────────
    try:
        _today_open  = float(df["Open"].iloc[-1])
        _today_close = float(df["Close"].iloc[-1])
        _today_high  = float(df["High"].iloc[-1])
        _today_low   = float(df["Low"].iloc[-1])
    except Exception:
        _today_open = _today_close = _today_high = _today_low = None

    _perf_pre = get_price_performance(df)
    _w52_lo = _perf_pre.get("w52_min") if _perf_pre else None
    _w52_hi = _perf_pre.get("w52_max") if _perf_pre else None

    _ohlc_items = [
        (T["close_label"], _today_close, "#e6edf3"),
        (T["open_label"],  _today_open,  "#e6edf3"),
        (T["day_high"],    _today_high,  "#58a6ff"),
        (T["day_low"],     _today_low,   "#dc2626"),
        (T["range_low"],   _w52_lo,      "#dc2626"),
        (T["range_high"],  _w52_hi,      "#58a6ff"),
    ]
    _ohlc_html = (
        "<style>.eq-ohlc{display:grid;grid-template-columns:repeat(6,1fr);gap:6px}"
        "@media(max-width:768px){.eq-ohlc{grid-template-columns:repeat(3,1fr)}}</style>"
        "<div class='eq-ohlc'>"
    )
    for _lbl, _val, _vc in _ohlc_items:
        _vstr = _fmt_money(_val, cs) if _val is not None else "\u2014"
        _ohlc_html += (
            f"<div style='background:#161b22;border:1px solid #21262d;"
            f"border-radius:9px;padding:8px 6px;text-align:center;'>"
            f"<div style='font-size:.65rem;color:#6e7681;margin-bottom:3px;'>{_lbl}</div>"
            f"<div style='font-size:.85rem;font-weight:700;color:{_vc};'>{_vstr}</div>"
            f"</div>"
        )
    _ohlc_html += "</div>"
    st.markdown(_ohlc_html, unsafe_allow_html=True)


def _quick_chart(df: pd.DataFrame, T: dict, cs: str = "R$") -> go.Figure:
    """
    Clean area chart for the interactive period view.
    Green/red gradient fill based on direction over the visible window.
    """
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    close = df["Close"]
    first = float(close.iloc[0])
    last  = float(close.iloc[-1])
    is_up = last >= first

    line_c = "#58a6ff" if is_up else "#dc2626"
    fill_c = "rgba(63,185,80,.18)" if is_up else "rgba(248,81,73,.18)"

    fig.add_trace(go.Scatter(
        x=df.index, y=close,
        mode="lines",
        line=dict(color=line_c, width=2.2, shape="spline", smoothing=.6),
        fill="tozeroy",
        fillcolor=fill_c,
        hovertemplate=f"%{{x|%d %b %Y %H:%M}}<br><b>{cs} %{{y:.2f}}</b><extra></extra>",
        name="",
    ))

    y_min = float(close.min())
    y_max = float(close.max())
    pad   = (y_max - y_min) * 0.12 if y_max > y_min else 1

    fig.update_layout(
        height=300,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6edf3", size=11),
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(
            showgrid=False, zeroline=False, showline=False,
            color="#8b949e", tickfont=dict(color="#6e7681", size=10),
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,.04)",
            zeroline=False, color="#8b949e",
            tickfont=dict(color="#6e7681", size=10),
            range=[y_min - pad, y_max + pad],
        ),
    )
    return fig


def _dividend_chart(dividends: pd.Series, ticker: str, T: dict, cs: str = "R$") -> go.Figure:
    annual = dividends.resample("YE").sum()
    avg = float(annual.mean())
    colors = ["#58a6ff" if v >= avg else "#e3b341" for v in annual.values]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=annual.index.year.tolist(), y=annual.values.tolist(),
        marker_color=colors,
        text=[f"{cs} {v:.2f}" for v in annual.values],
        textposition="outside",
        textfont=dict(color="#8b949e", size=10),
        hovertemplate=f"%{{x}}: {cs} %{{y:.2f}}<extra></extra>",
    ))
    fig.add_hline(
        y=avg, line_dash="dash", line_color="rgba(88,166,255,.6)", line_width=1.5,
        annotation_text=f"  {T['avg_label']}: {cs} {avg:.2f}",
        annotation_font=dict(color="#58a6ff", size=10),
    )
    fig.update_layout(
        title=dict(text=T["annual_divs"].format(t=ticker), font=dict(color="#8b949e", size=12)),
        height=300, showlegend=False, **_CHART_LAYOUT, xaxis=_AXIS, yaxis=_AXIS,
    )
    return fig


# ─── Login screen ─────────────────────────────────────────────────────────────

def _make_anon_user() -> dict:
    """Builds an anonymous user dict seeded from session state counters."""
    used = st.session_state.get("anon_queries_used", 0)
    return {
        "email": "anon",
        "is_admin": False,
        "credits": max(0, ANON_QUERY_LIMIT - used),
        "queries_used": used,
        "is_anonymous": True,
    }


def _render_top_auth_bar(user: dict, T: dict) -> None:
    """
    Minimal top-right auth strip (Apple Store style).
    Anon users see 'Entrar | Criar Conta'. Logged-in users see their email + Sair.
    """
    is_anon = user.get("is_anonymous", False)
    _pad, _slot = st.columns([6, 3])
    with _slot:
        if is_anon:
            b1, b2 = st.columns(2)
            with b1:
                if st.button(T["top_login_btn"], key="top_login_btn",
                             use_container_width=True):
                    st.session_state["show_login_form"] = True
                    st.rerun()
            with b2:
                if st.button(T["top_signup_btn"], key="top_signup_btn",
                             type="primary", use_container_width=True):
                    st.session_state["show_login_form"] = True
                    st.rerun()
        else:
            e_col, l_col = st.columns([2, 1])
            with e_col:
                st.markdown(
                    f"<div style='text-align:right;padding-top:6px;"
                    f"font-size:.82rem;color:#8b949e;'>"
                    f"{T['top_user_hi'].format(email=user.get('email','—'))}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with l_col:
                if st.button(T["logout_btn"], key="top_logout_btn",
                             use_container_width=True):
                    for k in ["user", "df", "dividends", "fundamentals",
                              "last_ticker", "last_period", "show_login_form"]:
                        st.session_state.pop(k, None)
                    st.session_state.user = _make_anon_user()
                    st.rerun()


def _render_inline_login(T: dict) -> None:
    """Inline login form that appears when user clicks Entrar/Criar Conta."""
    if not st.session_state.get("show_login_form"):
        return
    st.markdown(
        "<div style='background:#161b22;border:1px solid #d4af37;"
        "border-radius:12px;padding:20px 24px;margin-bottom:16px;'>"
        f"<div style='color:#d4af37;font-weight:800;font-size:1rem;"
        f"margin-bottom:10px;'>✨ {T['inline_login_title']}</div>",
        unsafe_allow_html=True,
    )
    c_email, c_btn, c_cancel = st.columns([4, 2, 2])
    with c_email:
        email = st.text_input(
            "E-mail", placeholder=T["email_placeholder"],
            key="inline_email_input", label_visibility="collapsed",
        )
    with c_btn:
        if st.button(T["enter_register"], type="primary",
                     use_container_width=True, key="inline_login_submit"):
            raw = (email or "").strip()
            if not raw or "@" not in raw or "." not in raw.split("@")[-1]:
                st.error(T["invalid_email"])
            else:
                with st.spinner(T["fetching"]):
                    u = get_or_create_user(raw.lower(), ADMIN_EMAIL)
                st.session_state.user = u
                st.session_state.show_login_form = False
                st.rerun()
    with c_cancel:
        if st.button(T["inline_cancel"], use_container_width=True,
                     key="inline_login_cancel"):
            st.session_state.show_login_form = False
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _render_paywall_card(T: dict) -> None:
    """Soft paywall shown to anon users who hit 0 credits."""
    st.markdown(
        f"<div style='background:linear-gradient(135deg,rgba(212,175,55,.12),"
        f"rgba(63,185,80,.08));border:2px solid #d4af37;border-radius:16px;"
        f"padding:40px 32px;margin:40px 0;text-align:center;'>"
        f"<div style='font-size:1.6rem;font-weight:900;color:#d4af37;"
        f"margin-bottom:14px;'>{T['paywall_title']}</div>"
        f"<div style='font-size:1rem;color:#e6edf3;line-height:1.6;"
        f"max-width:560px;margin:0 auto 22px;'>"
        f"{T['paywall_body'].format(limit=USER_QUERY_LIMIT)}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    _, _c, _ = st.columns([1, 2, 1])
    with _c:
        if st.button(T["paywall_cta"], type="primary",
                     use_container_width=True, key="paywall_cta_btn"):
            st.session_state["show_login_form"] = True
            st.rerun()


def render_login(T: dict) -> None:
    # Language picker (top-right of login page)
    _, lc = st.columns([4, 1])
    with lc:
        lang_names = [TRANSLATIONS[l]["lang_name"] for l in SUPPORTED_LANGS]
        cur_idx    = SUPPORTED_LANGS.index(st.session_state.get("lang", "pt"))
        chosen     = st.selectbox("lang", lang_names, index=cur_idx, label_visibility="collapsed", key="login_lang")
        new_lang   = SUPPORTED_LANGS[lang_names.index(chosen)]
        if new_lang != st.session_state.get("lang", "pt"):
            st.session_state.lang = new_lang
            st.rerun()

    _, col, _ = st.columns([1.2, 2, 1.2])
    with col:
        st.markdown(
            f'<div class="eg-login-hero">'
            f'<div class="eg-logo-wordmark">'
            f'<span class="eg-logo-gold">EQUITY</span>'
            f'<span class="eg-logo-white"> GUARD</span>'
            f'</div>'
            f'<div class="eg-tagline">{T["tagline"]}</div>'
            f'<div class="eg-login-features">'
            f'<span class="eg-feature-pill">📈 Value Investing</span>'
            f'<span class="eg-feature-pill">⚡ RSI + MA</span>'
            f'<span class="eg-feature-pill">💰 Dividendos</span>'
            f'<span class="eg-feature-pill">🌍 PT · EN · ES</span>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        email = st.text_input(
            "E-mail", placeholder=T["email_placeholder"],
            key="login_email_input", label_visibility="collapsed",
        )
        c1, c2 = st.columns([3, 2])
        with c1:
            btn_login = st.button(T["enter_register"], type="primary", use_container_width=True)
        with c2:
            btn_anon  = st.button(T["test_free"], use_container_width=True)

        if btn_login:
            raw = (email or "").strip()
            if not raw or "@" not in raw or "." not in raw.split("@")[-1]:
                st.error(T["invalid_email"])
            else:
                with st.spinner(T["fetching"]):
                    user = get_or_create_user(raw.lower(), ADMIN_EMAIL)
                st.session_state.user = user
                st.rerun()

        if btn_anon:
            used = st.session_state.get("anon_queries_used", 0)
            if used >= ANON_QUERY_LIMIT:
                st.warning(T["anon_limit_msg"].format(limit=USER_QUERY_LIMIT))
            else:
                st.session_state.user = {
                    "email": "anon", "is_admin": False,
                    "credits": ANON_QUERY_LIMIT - used,
                    "queries_used": used, "is_anonymous": True,
                }
                st.rerun()

        admin_hint = (
            "<br>⚙️ Dev: set <code>ADMIN_EMAIL</code> in <code>.env</code>"
            if not ADMIN_EMAIL else ""
        )
        st.markdown(
            f'<div class="eg-login-footer">'
            f'🔒 {T["tagline"]}{admin_hint}<br>'
            f'{USER_QUERY_LIMIT} créditos no cadastro · v{APP_VERSION}'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="eg-disclaimer">{T["disclaimer"]}</div>',
            unsafe_allow_html=True,
        )


# ─── Sidebar ──────────────────────────────────────────────────────────────────

def render_sidebar(user: dict, T: dict) -> tuple:
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center;padding:.5rem 0 .8rem;">'
            '<span style="font-size:1.6rem;font-weight:900;letter-spacing:-1px;">'
            '<span style="color:#d4af37;">EQUITY</span>'
            '<span style="color:#e6edf3;"> GUARD</span>'
            '</span></div>',
            unsafe_allow_html=True,
        )

        # ── Language selector (top right) ────────────────────────────────────
        lang_names = [TRANSLATIONS[l]["lang_name"] for l in SUPPORTED_LANGS]
        cur_idx    = SUPPORTED_LANGS.index(st.session_state.get("lang", "pt"))
        chosen     = st.selectbox("lang_sb", lang_names, index=cur_idx, label_visibility="collapsed", key="sb_lang")
        new_lang   = SUPPORTED_LANGS[lang_names.index(chosen)]
        if new_lang != st.session_state.get("lang", "pt"):
            st.session_state.lang = new_lang
            st.rerun()

        # Credit badge
        is_admin = user.get("is_admin", False)
        is_anon  = user.get("is_anonymous", False)
        lbl = T["access_master"] if is_admin else (
            T["anon_label"].format(c=user.get("credits", 0))
            if is_anon else
            T["credits_label"].format(c=user.get("credits", 0), limit=USER_QUERY_LIMIT)
        )
        badge_style = "background:rgba(212,175,55,.18);border-color:#d4af37;" if is_admin else ""
        st.markdown(
            f'<div class="eg-credit-badge" style="{badge_style}">{lbl}</div>',
            unsafe_allow_html=True,
        )
        if not is_admin and not is_anon:
            _credits_left = user.get("credits", 0)
            pct   = max(0, min(int(_credits_left / USER_QUERY_LIMIT * 100), 100))
            bar_c = "#58a6ff" if pct > 50 else ("#e3b341" if pct > 20 else "#dc2626")
            st.markdown(
                f'<div style="background:#21262d;border-radius:20px;height:5px;margin:4px 0 10px;">'
                f'<div style="background:{bar_c};width:{pct}%;height:100%;border-radius:20px;"></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Signup CTA for anonymous users
        if is_anon:
            if st.button(
                T["sidebar_signup_cta"].format(limit=USER_QUERY_LIMIT),
                use_container_width=True, type="primary",
                key="sb_signup_cta",
            ):
                st.session_state["show_login_form"] = True
                st.rerun()

        # Admin panel (only for admin users)
        if is_admin:
            with st.expander(T["admin_panel_title"]):
                _all_users = get_all_users()
                if _all_users:
                    _df_admin = pd.DataFrame([{
                        T["admin_col_email"]:   u["email"],
                        T["admin_col_login"]:   u.get("last_login", "—")[:19].replace("T", " "),
                        T["admin_col_queries"]: u.get("queries_used", 0),
                        T["admin_col_credits"]: "∞" if u.get("credits") == -1 else u.get("credits", 0),
                        T["admin_col_admin"]:   "✅" if u.get("is_admin") else "—",
                    } for u in _all_users])
                    st.dataframe(_df_admin, use_container_width=True, hide_index=True)
                    _csv = _df_admin.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        T["admin_csv_btn"],
                        data=_csv,
                        file_name=f"equity_guard_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    st.caption(T["admin_no_users"])

            with st.expander(T["admin_access_title"], expanded=False):
                _a_stats = get_stats()
                st.markdown(
                    f"<div style='display:flex;gap:12px;margin-bottom:8px;'>"
                    f"<div style='flex:1;background:#161b22;border:1px solid #30363d;"
                    f"border-radius:8px;padding:8px;text-align:center;'>"
                    f"<div style='font-size:.65rem;color:#6e7681;'>{T['admin_total']}</div>"
                    f"<div style='font-size:1.1rem;font-weight:800;color:#d4af37;'>"
                    f"{_a_stats['total']:,}</div></div>"
                    f"<div style='flex:1;background:#161b22;border:1px solid #30363d;"
                    f"border-radius:8px;padding:8px;text-align:center;'>"
                    f"<div style='font-size:.65rem;color:#6e7681;'>{T['admin_today']}</div>"
                    f"<div style='font-size:1.1rem;font-weight:800;color:#58a6ff;'>"
                    f"{_a_stats['today']:,}</div></div></div>",
                    unsafe_allow_html=True,
                )
                _daily = get_daily_series(30)
                if _daily:
                    _df_visits = pd.DataFrame(_daily, columns=[T["admin_chart_date"], T["admin_chart_visits"]])
                    _df_visits[T["admin_chart_date"]] = pd.to_datetime(_df_visits[T["admin_chart_date"]])
                    st.bar_chart(_df_visits.set_index(T["admin_chart_date"]), height=150)

        st.divider()

        # ══════════════════════════════════════════════════════════════════════
        # 1. MACRO PANEL — USD/BRL (logo após Cadastre-se)
        # ══════════════════════════════════════════════════════════════════════
        _render_macro_panel(T)

        # ══════════════════════════════════════════════════════════════════════
        # 2. HUB DE PREVIDÊNCIA — PrevDow completo, NitroPrev só com botão
        # de acesso (indices do IFM ocultos ate termos autorizacao formal).
        # ══════════════════════════════════════════════════════════════════════
        st.markdown('<div id="sidebar-prevdow"></div>', unsafe_allow_html=True)
        _render_prevdow_panel(T)
        _render_nitro_panel(T)

        st.divider()

        # ══════════════════════════════════════════════════════════════════════
        # 3. ANALYSIS INPUTS
        # ══════════════════════════════════════════════════════════════════════
        if "eg_ticker_input" not in st.session_state:
            st.session_state["eg_ticker_input"] = "BBAS3"

        _email_for_list = user.get("email", "") if not user.get("is_anonymous") else ""
        _user_favs = get_favorites(_email_for_list) if _email_for_list else []
        _user_hist = get_history(_email_for_list) if _email_for_list else []
        _all_options = sorted(set(ALL_TICKERS_B3 + _user_favs + _user_hist))

        _default = st.session_state.get("eg_ticker_input", "BBAS3").upper().strip()
        if _default not in _all_options:
            _all_options.append(_default)
            _all_options.sort()
        _default_idx = _all_options.index(_default)

        st.markdown(f'<div class="eg-section-header">{T["section_analysis"]}</div>', unsafe_allow_html=True)
        _sel_col, _custom_col = st.columns([3, 2])
        with _sel_col:
            ticker = st.selectbox(
                T["ticker_label"],
                options=_all_options,
                index=_default_idx,
                key="eg_ticker_select",
            )
        with _custom_col:
            _custom = st.text_input(
                T.get("custom_ticker_label", "Outro ticker"),
                placeholder="AAPL, HSBA.L…",
                key="eg_custom_ticker",
            ).upper().strip()
        if _custom:
            ticker = _custom
            st.session_state["eg_ticker_input"] = _custom
        else:
            st.session_state["eg_ticker_input"] = ticker
        period = st.selectbox(
            T["period_label"], ["1y", "2y", "3y", "5y"], index=1,
            format_func=lambda x: T["period_opts"][x],
        )
        target_yield = st.slider(T["yield_slider"], 4.0, 12.0, 6.0, .5) / 100
        _clicked_btn = st.button(T["analyze_btn"], use_container_width=True, type="primary")
        clicked = _clicked_btn or st.session_state.pop("_eg_auto_analyze", False)

        # ══════════════════════════════════════════════════════════════════════
        # 4. MEU TERMINAL — Watchlist + Recent History (logged-in only)
        # ══════════════════════════════════════════════════════════════════════
        st.markdown(
            f"<div style='color:#d4af37;font-weight:800;font-size:.92rem;"
            f"letter-spacing:.3px;text-transform:uppercase;margin:16px 0 4px;'>"
            f"{T['my_terminal_title']}</div>",
            unsafe_allow_html=True,
        )
        if not is_anon:
            _user_email = user.get("email", "")
            _favs = get_favorites(_user_email)
            _hist = get_history(_user_email)

            st.markdown(
                f'<div class="eg-section-header" style="margin-top:8px;">'
                f'{T["watchlist_title"]}</div>',
                unsafe_allow_html=True,
            )
            if _favs:
                for _f in _favs:
                    if st.button(
                        f"⭐ {_f}", key=f"sb_fav_{_f}",
                        use_container_width=True,
                    ):
                        st.session_state["eg_ticker_input"] = _f
                        st.session_state["eg_custom_ticker"] = ""
                        st.session_state["_eg_auto_analyze"] = True
                        st.rerun()
            else:
                st.caption(T["no_favorites"])

            st.markdown(
                f'<div class="eg-section-header" style="margin-top:14px;">'
                f'{T["history_title"]}</div>',
                unsafe_allow_html=True,
            )
            if _hist:
                for _h in _hist[:10]:
                    if st.button(
                        f"🕐 {_h}", key=f"sb_hist_{_h}",
                        use_container_width=True,
                    ):
                        st.session_state["eg_ticker_input"] = _h
                        st.session_state["eg_custom_ticker"] = ""
                        st.session_state["_eg_auto_analyze"] = True
                        st.rerun()
            else:
                st.caption(T["no_history"])
        else:
            st.markdown(
                f"<div style='background:#161b22;border:1px dashed #30363d;"
                f"border-radius:8px;padding:10px 14px;margin-top:8px;"
                f"font-size:.78rem;color:#8b949e;text-align:center;'>"
                f"{T['anon_personal_msg']}</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        # ══════════════════════════════════════════════════════════════════════
        # 3. LAYOUT TOGGLE — right below language
        # ══════════════════════════════════════════════════════════════════════
        _layout = st.radio(
            T["layout_mode_label"],
            [T["layout_always"], T["layout_compact"]],
            index=0 if not st.session_state.get("sidebar_compact") else 1,
            horizontal=True,
            key="sidebar_layout_radio",
        )
        st.session_state["sidebar_compact"] = (_layout == T["layout_compact"])
        _compact = st.session_state["sidebar_compact"]

        st.divider()

        # ══════════════════════════════════════════════════════════════════════
        # 4. BUY SIGNALS + 5. PREFERRED SECTORS
        # ══════════════════════════════════════════════════════════════════════
        # ── Signal rows HTML ───────────────────────────────────────────────────
        _sig_colors = {
            "strong_buy": "#58a6ff",
            "buy":        "#56d364",
            "wait":       "#d29922",
            "neutral":    "#58a6ff",
            "avoid":      "#dc2626",
        }
        _signal_rows_html = "".join(
            f"<div style='display:flex;align-items:center;gap:6px;padding:3px 0;'>"
            f"<span style='font-size:.9rem;'>{emoji}</span>"
            f"<span style='color:{_sig_colors[key]};font-weight:700;font-size:.78rem;"
            f"white-space:nowrap;'>{label}</span>"
            f"<span style='color:#6e7681;font-size:.73rem;'>{cond}</span>"
            f"</div>"
            for key, (emoji, label, cond) in T["signal_conditions"].items()
        )

        # ── Sector badges HTML ─────────────────────────────────────────────────
        _sec_colors = [
            ("#388bfd", "rgba(56,139,253,.12)"),
            ("#f0883e", "rgba(240,136,62,.12)"),
            ("#56d364", "rgba(86,211,100,.12)"),
            ("#bc8cff", "rgba(188,140,255,.12)"),
            ("#ff7b72", "rgba(255,123,114,.12)"),
        ]
        _sector_badges_html = (
            "<div style='display:flex;flex-wrap:wrap;gap:5px;margin-top:4px;'>"
            + "".join(
                f"<span style='display:inline-block;padding:2px 9px;border-radius:12px;"
                f"border:1px solid {_sec_colors[i][0]};background:{_sec_colors[i][1]};"
                f"color:{_sec_colors[i][0]};font-size:.74rem;font-weight:600;'>"
                f"{emoji} {name}</span>"
                for i, (emoji, name) in enumerate(T["sector_names"])
            )
            + "</div>"
        )

        # ── Render: always-visible or compact expanders ────────────────────────
        if _compact:
            with st.expander(T["section_signals"], expanded=False):
                st.markdown(_signal_rows_html, unsafe_allow_html=True)
            with st.expander(T["section_sectors"], expanded=False):
                st.markdown(_sector_badges_html, unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="eg-section-header">{T["section_signals"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(_signal_rows_html, unsafe_allow_html=True)
            st.markdown(
                f'<div class="eg-section-header" style="margin-top:10px;">{T["section_sectors"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(_sector_badges_html, unsafe_allow_html=True)

        st.divider()

        # Logout only for logged-in (non-anonymous) users
        if not is_anon:
            if st.button(T["logout_btn"], use_container_width=True, key="sb_logout_btn"):
                for k in ["user", "df", "dividends", "fundamentals",
                          "last_ticker", "last_period"]:
                    st.session_state.pop(k, None)
                st.session_state.user = _make_anon_user()
                st.rerun()

        st.caption(T["data_source"].format(version=APP_VERSION))

    return ticker, period, target_yield, clicked


# ─── Health row helper ────────────────────────────────────────────────────────

def _health_row(icon: str, label: str, hint: str, value_str: str, ok, tooltip: str = "") -> None:
    if ok is True:
        bg, vc, border = "rgba(63,185,80,.08)", "#58a6ff", "rgba(63,185,80,.25)"
    elif ok is False:
        bg, vc, border = "rgba(248,81,73,.08)", "#dc2626", "rgba(248,81,73,.25)"
    else:
        bg, vc, border = "#161b22", "#8b949e", "#30363d"
    title_attr = f' title="{tooltip}"' if tooltip else ""
    cursor_attr = " cursor:help;" if tooltip else ""
    st.markdown(
        f"<div class='eg-health-row' style='background:{bg};border-color:{border};"
        f"{cursor_attr}'{title_attr}>"
        f"<span>{icon} <b>{label}</b> "
        f"<span style='color:#6e7681;font-size:.76rem;'>{hint}</span></span>"
        f"<span style='color:{vc};font-weight:700;'>{value_str}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ─── Main analysis ────────────────────────────────────────────────────────────

def render_analysis(user: dict, ticker: str, period: str, target_yield: float,
                    clicked: bool, T: dict) -> None:

    key_changed = (
        st.session_state.get("last_ticker") != ticker
        or st.session_state.get("last_period") != period
    )
    should_load = clicked or key_changed or "df" not in st.session_state

    # ── Demo / lazy-loading gate ──────────────────────────────────────────────
    # The default ticker (DEMO_TICKER) loads once for free on first visit —
    # it is the app's "business card". Credit is only charged when the user
    # explicitly clicks "Analisar" or changes to a different ticker.
    _is_demo_free = (
        ticker.upper() == DEMO_TICKER
        and not clicked
        and "df" not in st.session_state   # truly first render
    )

    # ── Credit gate ───────────────────────────────────────────────────────────
    if should_load and not _is_demo_free and not has_credits(user):
        if user.get("is_anonymous"):
            _render_paywall_card(T)
        else:
            render_payment_page(user, T)
        st.stop()

    # ── Data fetch ────────────────────────────────────────────────────────────
    if should_load:
        _label = T["loading"].format(t=ticker)
        if _is_demo_free:
            _label = f"{T['demo_badge']} — {_label}"
        with st.spinner(_label):
            df, dividends, fundamentals = _fetch_full_data(ticker, period=period)

        if df is None or df.empty:
            st.error(T["not_found"].format(t=ticker))
            return

        # Consume credit — skip for the free demo load
        if not _is_demo_free:
            if not user.get("is_admin") and not user.get("is_anonymous"):
                use_credit(user["email"])
                refreshed = load_user(user["email"])
                if refreshed:
                    st.session_state.user = refreshed
                    user = refreshed
            elif user.get("is_anonymous"):
                used = st.session_state.get("anon_queries_used", 0) + 1
                st.session_state.anon_queries_used = used
                st.session_state.user["credits"]      = max(0, user["credits"] - 1)
                st.session_state.user["queries_used"] = used

        st.session_state.update(df=df, dividends=dividends, fundamentals=fundamentals,
                                 last_ticker=ticker, last_period=period)

        # Auto-track recent history for logged-in (non-anonymous) users
        if not _is_demo_free and not user.get("is_anonymous"):
            add_history(user["email"], ticker.upper().strip())

    df: pd.DataFrame = st.session_state["df"]
    dividends        = st.session_state["dividends"]
    fundamentals: dict = st.session_state["fundamentals"]

    # ── Currency symbol (USD/GBP/EUR/BRL…) ────────────────────────────────────
    cs = _currency_symbol(fundamentals.get("currency", "BRL"))

    # ── Ticker chip HTML — repetido antes de cada secao para que prints
    #    da pagina sempre mostrem qual acao esta sendo analisada.
    _chip_name = fundamentals.get("name", ticker)
    _chip_sym = normalize_ticker(ticker)
    _ticker_chip_html = (
        f'<div class="eg-ticker-chip">'
        f'{_chip_name}'
        f'<span class="eg-ticker-chip-sym">{_chip_sym}</span>'
        f'</div>'
    )

    # ── Calculations ──────────────────────────────────────────────────────────
    avg_div = calculate_avg_dividends(dividends) if dividends is not None else 0.0
    teto    = calculate_teto_barsi(avg_div, target_yield)
    price   = fundamentals.get("current_price") or float(df["Close"].iloc[-1])
    margin  = calculate_safety_margin(price, teto)
    health  = check_health_indicators(fundamentals)
    rsi_now = get_current_rsi(df)
    trend   = analyze_trend(df)
    signal  = generate_buy_signal(price, teto, rsi_now)
    is_best, best_name = identify_best_sector(
        fundamentals.get("sector", ""), fundamentals.get("industry", "")
    )

    # Translate signal
    sk          = signal["signal_key"]
    action_text = T["signals"][sk]
    desc_text   = T["signal_descs"][sk].format(rsi=rsi_now)
    yield_pct   = target_yield * 100

    # ── Company header ────────────────────────────────────────────────────────
    c_title, c_sig = st.columns([3, 1])
    with c_title:
        name = fundamentals.get("name", ticker)
        best_badge = (
            f'<span class="eg-best-badge">⭐ {T["best_badge"]}</span>'
            if is_best else ""
        )
        dev_badge = (
            f'<span class="eg-dev-badge">{T["dev_badge"]}</span>'
            if user.get("is_admin") else ""
        )

        # Favorite toggle — star button next to the company name
        _is_anon    = user.get("is_anonymous", False)
        _ticker_key = ticker.upper().strip()
        _is_fav     = (
            _ticker_key in get_favorites(user.get("email", ""))
            if not _is_anon else False
        )
        _name_col, _star_col = st.columns([9, 1])
        with _name_col:
            st.markdown(
                f"<h3 style='margin:0 0 4px;display:flex;align-items:center;"
                f"gap:6px;flex-wrap:wrap;font-size:1.25rem;font-weight:800;'>"
                f"<span>{name}</span>"
                f"<span class='eg-ticker-chip-sym'>{normalize_ticker(ticker)}</span>"
                f"{best_badge}{dev_badge}"
                f"</h3>"
                f"<div style='color:#8b949e;font-size:.8rem;margin-bottom:6px;'>"
                f"{fundamentals.get('sector','—')} › {fundamentals.get('industry','—')}"
                f"</div>",
                unsafe_allow_html=True,
            )
        with _star_col:
            _star_icon = "⭐" if _is_fav else "☆"
            _star_help = T["fav_remove_help"] if _is_fav else T["fav_add_help"]
            if st.button(_star_icon, key="eg_fav_toggle", help=_star_help):
                if _is_anon:
                    st.toast(T["fav_anon_toast"])
                elif _is_fav:
                    remove_favorite(user["email"], _ticker_key)
                    st.toast(T["fav_removed_toast"].format(ticker=_ticker_key))
                    st.rerun()
                else:
                    add_favorite(user["email"], _ticker_key)
                    st.toast(T["fav_added_toast"].format(ticker=_ticker_key))
                    st.rerun()
    with c_sig:
        st.markdown(
            f"<div class='eg-signal' style='background:{signal['bg_color']};color:{signal['color']};'>"
            f"{signal['emoji']} {action_text}</div>"
            f"<div style='font-size:.76rem;color:#8b949e;text-align:center;margin-top:5px;'>"
            f"{desc_text}</div>",
            unsafe_allow_html=True,
        )

    # ── Sticky ticker bar (mobile) ───────────────────────────────────────────
    _ticker_display = normalize_ticker(ticker)
    _price_display = f"{cs} {price:.2f}"
    import streamlit.components.v1 as _sticky_comp
    _sticky_comp.html("""
    <script>
    (function() {
        var doc = window.parent.document;
        if (doc.getElementById('eg-sticky-ticker')) return;
        var bar = doc.createElement('div');
        bar.id = 'eg-sticky-ticker';
        bar.innerHTML = '""" + _ticker_display + " | " + _price_display + """';
        bar.style.cssText = 'display:none;position:fixed;top:0;left:0;right:0;z-index:99998;'
            + 'background:#161b22;border-bottom:1px solid #d4af37;'
            + 'padding:6px 16px;font-size:13px;font-weight:800;color:#d4af37;'
            + 'text-align:center;font-family:Inter,system-ui,sans-serif;';
        doc.body.appendChild(bar);
        function check() { bar.style.display = window.parent.innerWidth <= 768 ? 'block' : 'none'; }
        check();
        window.parent.addEventListener('resize', check);
    })();
    </script>
    """, height=0)

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # 📈 INTERACTIVE QUOTE — right below the signal (primary scroll experience)
    # ══════════════════════════════════════════════════════════════════════════
    # Sem ticker chip aqui: o cabecalho da empresa acima ja identifica a acao.
    st.markdown('<div class="eg-nav-anchor" id="sec-cotacao"></div>', unsafe_allow_html=True)
    _render_interactive_quote(ticker, df, T, cs)

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # 🔮 FUTURE-FOCUS BLOCK — projection + monthly map at the top of the page
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="eg-nav-anchor" id="sec-projecao"></div>' + _ticker_chip_html, unsafe_allow_html=True)
    _fut_left, _fut_right = st.columns([3, 2])

    with _fut_left:
        st.markdown(
            f'<div class="eg-section-header">🔮 {T["projection_title"]}</div>',
            unsafe_allow_html=True,
        )
        if avg_div > 0:
            growth = st.slider(T["projection_growth"], 0.0, 20.0, 5.0, .5, key="div_growth") / 100
            proj   = project_dividends(avg_div, years=5, growth_rate=growth)
            rows   = [
                {
                    T["year_col"]:           f"+{yr}",
                    T["div_projected"]:      f"{cs} {dv:.2f}",
                    T["ceiling_projected"].format(pct=yield_pct): f"{cs} {dv/target_yield:.2f}",
                    T["yield_on_price"]:     f"{dv/price*100:.2f}%",
                    T["potential_gain"]:     f"{(dv/target_yield - price)/price*100:+.1f}%",
                }
                for yr, dv in proj.items()
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info(T["no_projection"])

    with _fut_right:
        st.markdown(
            _ticker_chip_html + f'<div class="eg-section-header">{T["month_map_title"]}</div>',
            unsafe_allow_html=True,
        )

        # ── Smart frequency banner (above the monthly grid) ───────────────────
        _freq      = detect_dividend_frequency(dividends)
        _freq_key  = _freq.get("key", "none")
        _freq_text = T["freq_banners"].get(_freq_key, "")
        if _freq_text:
            st.markdown(
                f"<div style='background:rgba(88,166,255,.10);"
                f"border:1px solid rgba(88,166,255,.35);border-radius:8px;"
                f"padding:9px 14px;margin-bottom:10px;font-size:.82rem;color:#e6edf3;'>"
                f"{_freq_text}</div>",
                unsafe_allow_html=True,
            )

        _pattern = get_dividend_month_pattern(dividends)
        _max_cnt = max(_pattern.values()) if _pattern else 0
        if _max_cnt > 0:
            _months_lbl = T["month_names_short"]
            _now_m      = pd.Timestamp.now().month
            _grid_html  = "<div style='display:grid;grid-template-columns:repeat(6,1fr);gap:5px;margin-top:8px;'>"
            for _i, _mn in enumerate(_months_lbl, start=1):
                _cnt    = _pattern.get(_i, 0)
                _is_now = (_i == _now_m)
                _alpha  = (_cnt / _max_cnt) if _max_cnt else 0
                if _cnt > 0:
                    _bg     = f"rgba(212,175,55,{0.15 + _alpha*0.45:.2f})"
                    _border = "#d4af37"
                    _fg     = "#e6edf3"
                else:
                    _bg     = "#161b22"
                    _border = "#30363d"
                    _fg     = "#6e7681"
                _ring = "box-shadow:0 0 0 2px #58a6ff;" if _is_now else ""
                _grid_html += (
                    f"<div style='background:{_bg};border:1px solid {_border};"
                    f"border-radius:8px;padding:8px 4px;text-align:center;{_ring}'>"
                    f"<div style='font-size:.68rem;color:{_fg};font-weight:600;'>{_mn}</div>"
                    f"<div style='font-size:.95rem;color:{_fg};font-weight:700;margin-top:2px;'>"
                    f"{_cnt if _cnt else '—'}</div>"
                    f"</div>"
                )
            _grid_html += "</div>"
            st.markdown(_grid_html, unsafe_allow_html=True)

            _hist_months = [m for m, c in _pattern.items() if c > 0]
            _future      = [m for m in _hist_months if m >= _now_m]
            _next_m      = min(_future) if _future else min(_hist_months)
            _next_name   = _months_lbl[_next_m - 1]
            st.markdown(
                f"<div style='background:rgba(63,185,80,.08);border:1px solid rgba(63,185,80,.3);"
                f"border-radius:8px;padding:8px 14px;margin-top:10px;font-size:.82rem;color:#e6edf3;'>"
                f"{T['next_likely'].format(m=_next_name)}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info(T["no_month_pattern"])

    # ══════════════════════════════════════════════════════════════════════════
    # 🎯 INCOME GOAL CALCULATOR
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="eg-nav-anchor" id="sec-dividendos"></div>' + _ticker_chip_html, unsafe_allow_html=True)
    st.markdown(
        f'<div class="eg-section-header">{T["goal_title"]}</div>',
        unsafe_allow_html=True,
    )
    if avg_div > 0 and price and price > 0:
        _lang = st.session_state.get("lang", "pt")
        _br_locale = _lang in ("pt", "es")

        def _parse_money(s: str, default: float = 1000.0) -> float:
            """Aceita 'R$ 1.000,00', 'US$ 1,000.00', '1000', etc."""
            if not s:
                return default
            s = str(s).strip()
            for p in ("R$", "US$", "U$S", "€", "£", "$", " "):
                s = s.replace(p, "")
            if "," in s and "." in s:
                if s.rfind(",") > s.rfind("."):
                    s = s.replace(".", "").replace(",", ".")
                else:
                    s = s.replace(",", "")
            elif "," in s and s.count(",") == 1:
                s = s.replace(",", ".")
            try:
                return max(0.0, float(s))
            except ValueError:
                return default

        if _br_locale:
            _default_str = f"{cs} 1.000,00"
        else:
            _default_str = f"{cs} 1,000.00"

        _g1, _g2, _g3 = st.columns([2, 2, 3])
        with _g1:
            _goal_str = st.text_input(
                T["goal_input_label"],
                value=st.session_state.get("goal_target_str", _default_str),
                key="goal_target_str",
                placeholder=_default_str,
            )
            _goal_target = _parse_money(_goal_str, default=1000.0)
        with _g2:
            _freq_opts = T["goal_freq_options"]
            _freq_idx  = st.selectbox(
                T["goal_freq_label"],
                options=list(range(len(_freq_opts))),
                format_func=lambda i: _freq_opts[i],
                index=0, key="goal_freq",
            )
        with _g3:
            _mult_map     = [12, 4, 1]   # mês, trimestre, ano → fator anual
            _annual_need  = _goal_target * _mult_map[_freq_idx]
            _shares_raw   = _annual_need / avg_div if avg_div > 0 else 0
            # Round UP to nearest 100 (standard B3 lot size)
            _shares_lot   = int(math.ceil(_shares_raw / 100.0) * 100) if _shares_raw > 0 else 0
            _invest_total = _shares_lot * price
            st.markdown(
                f"<div style='background:rgba(212,175,55,.10);border:1px solid #d4af37;"
                f"border-radius:10px;padding:14px 18px;margin-top:28px;font-size:.9rem;"
                f"color:#e6edf3;line-height:1.55;text-align:right;'>"
                f"{T['goal_result'].format(shares=_fmt_int(_shares_lot, cs), money=_fmt_money(_invest_total, cs))}"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info(T["goal_no_data"])

    st.divider()

    # ── Key metrics ───────────────────────────────────────────────────────────
    st.markdown('<div class="eg-nav-anchor" id="sec-metricas"></div>' + _ticker_chip_html, unsafe_allow_html=True)
    st.markdown(f'<div class="eg-section-header">{T["current_price"][:2]} {T["nav_metricas"]}</div>', unsafe_allow_html=True)
    dy = fundamentals.get("dividend_yield")
    _dy_s = f"{dy*100:.2f}%" if dy else T["na"]
    _teto_s = f"{cs} {teto:.2f}" if teto > 0 else T["na"]
    _margin_s = f"{margin:.1f}%" if teto > 0 else T["na"]
    _margin_c = "#58a6ff" if margin > 0 else "#dc2626"
    _margin_d = T["below_delta"] if margin > 0 else T["above_delta"]
    _rsi_c = "#dc2626" if rsi_now > 70 else ("#58a6ff" if rsi_now < 30 else "#8b949e")
    _rsi_lbl = T["overbought"] if rsi_now > 70 else (T["oversold"] if rsi_now < 30 else T["neutral_rsi"])
    ceiling_label = T["ceiling_price"].format(pct=yield_pct)

    _met_items = [
        (T["current_price"], f"{cs} {price:.2f}", "", "#d4af37"),
        (ceiling_label, _teto_s, "", "#e6edf3"),
        (T["safety_margin"], _margin_s, _margin_d, _margin_c),
        (T["dividend_yield"], _dy_s, "", "#58a6ff"),
        (T["rsi_label"], f"{rsi_now:.1f}", _rsi_lbl, _rsi_c),
    ]
    _met_html = (
        "<style>.eq-met{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}"
        "@media(max-width:768px){.eq-met{grid-template-columns:repeat(3,1fr)}}</style>"
        "<div class='eq-met'>"
    )
    for _ml, _mv, _md, _mc in _met_items:
        _delta_html = f"<div style='font-size:.65rem;color:{_mc};margin-top:2px;'>{_md}</div>" if _md else ""
        _met_html += (
            f"<div style='background:#161b22;border:1px solid #30363d;"
            f"border-radius:10px;padding:10px 8px;text-align:center;'>"
            f"<div style='font-size:.62rem;color:#6e7681;margin-bottom:3px;'>{_ml}</div>"
            f"<div style='font-size:1rem;font-weight:800;color:{_mc};'>{_mv}</div>"
            f"{_delta_html}</div>"
        )
    _met_html += "</div>"
    st.markdown(_met_html, unsafe_allow_html=True)

    if teto > 0:
        if margin > 0:
            st.markdown(
                f'<div class="eg-margin-ok">'
                f'{T["below_ceiling"].format(m=margin)}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="eg-margin-risk">'
                f'{T["above_ceiling"].format(m=abs(margin))}</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Performance Report ────────────────────────────────────────────────────
    st.markdown(_ticker_chip_html + f'<div class="eg-section-header">{T["perf_title"]}</div>', unsafe_allow_html=True)
    _perf = get_price_performance(df)
    if _perf:
        _perf_data = [
            (T["perf_1d"],      _perf.get("yesterday"),  _perf.get("chg_1d")),
            (T["perf_7d"],      _perf.get("price_7d"),   _perf.get("chg_7d")),
            (T["perf_30d"],     _perf.get("price_30d"),  _perf.get("chg_30d")),
            (T["perf_52w_min"], _perf.get("w52_min"),    None),
            (T["perf_52w_max"], _perf.get("w52_max"),    None),
        ]
        _perf_html = (
            "<style>.eq-perf{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}"
            "@media(max-width:768px){.eq-perf{grid-template-columns:repeat(3,1fr)}}</style>"
            "<div class='eq-perf'>"
        )
        for _lbl, _ref, _chg in _perf_data:
            _clr = "#58a6ff" if (_chg is not None and _chg > 0) else (
                   "#dc2626" if (_chg is not None and _chg < 0) else "#8b949e")
            _chg_s = f"{_chg:+.1f}%" if _chg is not None else "\u2014"
            _ref_s = f"{cs} {_ref:.2f}" if _ref is not None else "\u2014"
            _perf_html += (
                f"<div style='background:#161b22;border:1px solid #21262d;"
                f"border-radius:10px;padding:8px 6px;text-align:center;'>"
                f"<div style='font-size:.65rem;color:#6e7681;margin-bottom:3px;'>{_lbl}</div>"
                f"<div style='font-size:.88rem;font-weight:700;color:#e6edf3;'>{_ref_s}</div>"
                f"<div style='font-size:.75rem;font-weight:700;color:{_clr};'>{_chg_s}</div>"
                f"</div>"
            )
        _perf_html += "</div>"
        st.markdown(_perf_html, unsafe_allow_html=True)
        _chg30 = _perf.get("chg_30d")
        _chg7  = _perf.get("chg_7d")
        _wmin  = _perf.get("w52_min")
        _wmax  = _perf.get("w52_max")
        if all(v is not None for v in [_chg30, _chg7, _wmin, _wmax]):
            _dir30 = T["perf_up"] if _chg30 > 0 else (T["perf_down"] if _chg30 < 0 else T["perf_flat"])
            _narr  = T["perf_narrative"].format(
                name=fundamentals.get("name", ticker),
                w52_min=_wmin, w52_max=_wmax,
                m30=_chg30, dir30=_dir30, w7=_chg7, cs=cs,
            )
            st.markdown(
                f"<div style='background:#161b22;border:1px solid #21262d;border-radius:8px;"
                f"padding:12px 16px;margin-top:10px;font-size:.88rem;color:#8b949e;'>{_narr}</div>",
                unsafe_allow_html=True,
            )

        # ── 52-Week Range Bar ─────────────────────────────────────────────────
        _w52_min = _perf.get("w52_min")
        _w52_max = _perf.get("w52_max")
        _curr    = _perf.get("current")
        if _w52_min and _w52_max and _curr and _w52_max > _w52_min:
            _pos_pct = max(0.0, min(100.0, (_curr - _w52_min) / (_w52_max - _w52_min) * 100))
            st.markdown(_ticker_chip_html, unsafe_allow_html=True)
            st.markdown(
                f"<div style='margin-top:4px;background:#161b22;border:1px solid #21262d;"
                f"border-radius:10px;padding:14px 20px;'>"
                f"<div style='font-size:.78rem;color:#d4af37;font-weight:700;"
                f"text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;'>"
                f"{T['range_52w_title']}</div>"
                f"<div style='display:flex;justify-content:space-between;align-items:flex-end;"
                f"font-size:.74rem;color:#6e7681;margin-bottom:6px;'>"
                f"<span>📉 {T['range_low']}<br>"
                f"<b style='color:#dc2626;font-size:.95rem;'>{cs} {_w52_min:.2f}</b></span>"
                f"<span style='text-align:center;'>💎 {T['current_price'][2:].strip()}<br>"
                f"<b style='color:#d4af37;font-size:1.05rem;'>{cs} {_curr:.2f}</b></span>"
                f"<span style='text-align:right;'>📈 {T['range_high']}<br>"
                f"<b style='color:#58a6ff;font-size:.95rem;'>{cs} {_w52_max:.2f}</b></span>"
                f"</div>"
                f"<div style='position:relative;height:12px;background:linear-gradient(90deg,"
                f"#58a6ff 0%,#e3b341 50%,#dc2626 100%);border-radius:6px;margin-top:10px;'>"
                f"<div style='position:absolute;left:{_pos_pct:.1f}%;top:-5px;"
                f"transform:translateX(-50%);width:5px;height:22px;background:#e6edf3;"
                f"border-radius:2px;box-shadow:0 0 8px rgba(255,255,255,.8);'></div>"
                f"</div>"
                f"<div style='text-align:center;font-size:.84rem;color:#8b949e;margin-top:10px;'>"
                f"{T['range_position'].format(p=_pos_pct)}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.caption(T["perf_no_data"])

    st.divider()

    # ── Financial health + Trend ──────────────────────────────────────────────
    st.markdown('<div class="eg-nav-anchor" id="sec-saude"></div>' + _ticker_chip_html, unsafe_allow_html=True)
    col_h, col_t = st.columns(2)

    with col_h:
        st.markdown(f'<div class="eg-section-header">{T["health_title"]}</div>', unsafe_allow_html=True)

        pv = health["payout_value"]
        dv = health["debt_ebitda_value"]
        rv = health["roe_value"]
        pe = fundamentals.get("pe_ratio")
        pb = fundamentals.get("pb_ratio")

        _is_bank_no_ebitda = (best_name == "Bancos" and dv is None)
        _health_items = [
            (f"📤 {T['payout']}", f"{pv:.1f}%" if pv is not None else T["na"], T["payout_hint"], "#e6edf3"),
            (f"🏦 {T['debt_ebitda']}",
             T["na"] if dv is None else f"{dv:.2f}×",
             "" if _is_bank_no_ebitda else T["debt_ebitda_hint"],
             "#8b949e" if dv is None else "#e6edf3"),
            (f"📊 {T['roe']}", f"{rv:.1f}%" if rv is not None else T["na"], T["roe_hint"], "#e6edf3"),
        ]
        if pe:
            _health_items.append((f"🔢 {T['pe_label']}", f"{pe:.1f}×", "", "#e6edf3"))
        if pb:
            _health_items.append((f"📚 {T['pb_label']}", f"{pb:.2f}×", "", "#e6edf3"))

        _health_html = (
            "<style>.eq-health{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}"
            "@media(max-width:768px){.eq-health{grid-template-columns:repeat(2,1fr)}}</style>"
            "<div class='eq-health'>"
        )
        for _hl, _hv, _hd, _hc in _health_items:
            _delta = f"<div style='font-size:.6rem;color:#6e7681;margin-top:2px;line-height:1.2;'>{_hd}</div>" if _hd else ""
            _health_html += (
                f"<div style='background:#161b22;border:1px solid #30363d;"
                f"border-radius:10px;padding:8px 6px;text-align:center;'>"
                f"<div style='font-size:.6rem;color:#6e7681;margin-bottom:3px;line-height:1.2;'>{_hl}</div>"
                f"<div style='font-size:.95rem;font-weight:800;color:{_hc};'>{_hv}</div>"
                f"{_delta}</div>"
            )
        _health_html += "</div>"
        st.markdown(_health_html, unsafe_allow_html=True)

        if _is_bank_no_ebitda:
            st.caption(T["bank_ebitda_note"])

    with col_t:
        st.markdown(f'<div class="eg-section-header">{T["trend_title"]}</div>', unsafe_allow_html=True)
        ov = trend["overall"]
        trend_map = {
            "TENDÊNCIA DE ALTA FORTE":  (T["trend_bull_strong"], "rgba(63,185,80,.12)",   "#58a6ff"),
            "TENDÊNCIA DE ALTA":        (T["trend_bull"],        "rgba(63,185,80,.07)",   "#56d364"),
            "TENDÊNCIA DE BAIXA FORTE": (T["trend_bear_strong"], "rgba(248,81,73,.12)",   "#dc2626"),
            "TENDÊNCIA DE BAIXA":       (T["trend_bear"],        "rgba(248,81,73,.07)",   "#ff6b6b"),
        }
        t_label, t_bg, t_color = trend_map.get(ov, (T["trend_neutral"], "#161b22", "#8b949e"))
        st.markdown(
            f"<div class='eg-trend-box' style='background:{t_bg};color:{t_color};'>{t_label}</div>",
            unsafe_allow_html=True,
        )

        # ── MM20 / MM200 cards (dados brutos) ─────────────────────────────────
        _ma20 = trend.get("ma20")
        _ma200 = trend.get("ma200")
        _lbl_short = T.get("ma_short", "MA20")
        _lbl_long = T.get("ma_long", "MA200")
        _ma_items = []
        for ma_val, ma_lbl in [(_ma20, _lbl_short), (_ma200, _lbl_long)]:
            if ma_val:
                diff = ((price - ma_val) / ma_val) * 100
                _diff_c = "#58a6ff" if diff > 0 else "#dc2626"
                _ma_items.append((ma_lbl, f"{cs} {ma_val:.2f}", f"{diff:+.1f}%", _diff_c))
        if _ma_items:
            _ma_html = (
                "<style>.eq-ma{display:grid;grid-template-columns:repeat(2,1fr);gap:6px;margin-top:8px}</style>"
                "<div class='eq-ma'>"
            )
            for _ml, _mv, _md, _mc in _ma_items:
                _ma_html += (
                    f"<div style='background:#161b22;border:1px solid #30363d;"
                    f"border-radius:10px;padding:8px 6px;text-align:center;'>"
                    f"<div style='font-size:.78rem;color:#ffffff;margin-bottom:4px;"
                    f"line-height:1.2;font-weight:800;letter-spacing:.4px;'>{_ml}</div>"
                    f"<div style='font-size:.95rem;font-weight:800;color:#e6edf3;'>{_mv}</div>"
                    f"<div style='font-size:.68rem;color:{_mc};margin-top:2px;font-weight:700;'>{_md}</div>"
                    f"</div>"
                )
            _ma_html += "</div>"
            st.markdown(_ma_html, unsafe_allow_html=True)

        # ── Veredito consolidado: cruz + explicacao "porque" ──────────────────
        _why = None
        if _ma20 and _ma200:
            _spread = ((_ma20 - _ma200) / _ma200) * 100
            if ov == "TENDÊNCIA DE ALTA FORTE":
                _why = (
                    f"A média dos últimos <b>20 dias</b> ({cs} {_ma20:.2f}) está <b>{_spread:+.1f}%</b> "
                    f"acima da média dos últimos <b>200 dias</b> ({cs} {_ma200:.2f}) — "
                    f"compradores dominam no curto e longo prazo."
                )
            elif ov == "TENDÊNCIA DE ALTA":
                _why = (
                    f"MA20 ({cs} {_ma20:.2f}) ligeiramente acima da MA200 ({cs} {_ma200:.2f}), "
                    f"diferença de <b>{_spread:+.1f}%</b> — momentum positivo, mas ainda moderado."
                )
            elif ov == "TENDÊNCIA DE BAIXA FORTE":
                _why = (
                    f"A média dos últimos <b>20 dias</b> ({cs} {_ma20:.2f}) está <b>{_spread:+.1f}%</b> "
                    f"abaixo da média dos últimos <b>200 dias</b> ({cs} {_ma200:.2f}) — "
                    f"vendedores pressionando tanto o curto quanto o longo prazo."
                )
            elif ov == "TENDÊNCIA DE BAIXA":
                _why = (
                    f"MA20 ({cs} {_ma20:.2f}) ligeiramente abaixo da MA200 ({cs} {_ma200:.2f}), "
                    f"diferença de <b>{_spread:+.1f}%</b> — pressão vendedora moderada."
                )
            else:
                _why = (
                    f"MA20 ({cs} {_ma20:.2f}) e MA200 ({cs} {_ma200:.2f}) praticamente coladas "
                    f"(<b>{_spread:+.1f}%</b>) — mercado sem direção clara no momento."
                )

        _cross_lbl = None
        _cross_bg = None
        _cross_border = None
        if trend.get("golden_cross"):
            _cross_lbl = T["golden_cross"]
            _cross_bg = "rgba(63,185,80,.10)"
            _cross_border = "#3fb950"
        elif trend.get("death_cross"):
            _cross_lbl = T["death_cross"]
            _cross_bg = "rgba(248,81,73,.10)"
            _cross_border = "#f85149"

        if _cross_lbl or _why:
            _header = (
                f"<div style='font-size:.86rem;font-weight:800;color:#e6edf3;margin-bottom:6px;'>"
                f"{_cross_lbl}</div>" if _cross_lbl else ""
            )
            _body = (
                f"<div style='font-size:.78rem;color:#c9d1d9;line-height:1.5;'>{_why}</div>"
                if _why else ""
            )
            _bg = _cross_bg or "#161b22"
            _border = _cross_border or t_color
            st.markdown(
                f"<div style='margin-top:10px;padding:10px 14px;background:{_bg};"
                f"border:1px solid {_border};border-radius:8px;'>"
                f"{_header}{_body}</div>",
                unsafe_allow_html=True,
            )

        rsi_bar_c = "#dc2626" if rsi_now > 70 else ("#58a6ff" if rsi_now < 30 else "#e3b341")
        st.markdown(
            f"<div style='margin-top:12px;'>"
            f"<span style='color:#8b949e;font-size:.82rem;'>RSI (14): </span>"
            f"<b style='color:{rsi_bar_c};'>{rsi_now:.1f}</b>"
            f"<div class='eg-rsi-track'>"
            f"<div class='eg-rsi-fill' style='background:{rsi_bar_c};width:{rsi_now:.0f}%;'></div>"
            f"</div>"
            f"<div class='eg-rsi-labels'>"
            f"<span>0 {T['oversold']}</span><span>50</span><span>{T['overbought']} 100</span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Main chart ────────────────────────────────────────────────────────────
    st.markdown('<div class="eg-nav-anchor" id="sec-tecnico"></div>' + _ticker_chip_html, unsafe_allow_html=True)
    st.markdown(f'<div class="eg-section-header">{T["chart_title"]}</div>', unsafe_allow_html=True)
    with st.expander(f"📘 {T['chart_help_title']}", expanded=True):
        st.markdown(
            f"<div style='font-size:.84rem;line-height:1.55;color:#c9d1d9;'>"
            f"{T['chart_help_body']}</div>",
            unsafe_allow_html=True,
        )

    # Seletor de periodo + agregacao. Intraday (5m/15m/1h) vai direto pra
    # _intraday_chart (sem Barsi/Zona/MM200 — MMs curtas MM9/MM21). Demais usam
    # o grafico principal com Barsi e MMs longas.
    # Layout: tupla = (label, period_arg, granularity, interval_for_fetch)
    _chart_options = [
        ("5m",            "1d",  "I", "5m"),   # so sessao atual
        ("15m",           "5d",  "I", "15m"),  # ultimos 5 pregoes
        ("1h",            "1mo", "I", "1h"),   # ultimo mes
        ("1M",            22,    "D", None),
        ("3M",            66,    "D", None),
        ("6M",            132,   "D", None),
        ("1A",            252,   "D", None),
        ("2A · semanal",  104,   "W", None),
        ("5A · semanal",  260,   "W", None),
        ("Tudo · mensal", None,  "M", None),
    ]
    _chart_period = st.radio(
        "Período do gráfico",
        options=[lbl for lbl, _, _, _ in _chart_options],
        index=4,  # 3M diario por default (posicao 4 agora que os intraday vieram antes)
        horizontal=True,
        key="chart_period_selector",
        label_visibility="collapsed",
    )
    _opt_map = {lbl: (arg, gran, interval) for lbl, arg, gran, interval in _chart_options}
    _period_arg, _granularity, _interval = _opt_map[_chart_period]

    try:
        if _granularity == "I":
            _df_intra = _fetch_intraday(ticker, _interval, _period_arg)
            if _df_intra is None or _df_intra.empty:
                st.warning(
                    f"Sem dados intraday disponiveis para {_chart_period}. "
                    f"Tente um periodo maior (1M, 3M...) ou aguarde o mercado abrir."
                )
            else:
                st.plotly_chart(
                    _intraday_chart(_df_intra, T, cs=cs, interval_label=_chart_period),
                    use_container_width=True,
                    config={"displayModeBar": False, "displaylogo": False},
                )
        else:
            if _granularity == "D":
                _df_chart = df.tail(_period_arg) if _period_arg else df
            else:
                _rule = "W-FRI" if _granularity == "W" else "ME"
                _agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
                if "Volume" in df.columns:
                    _agg["Volume"] = "sum"
                _df_resampled = df.resample(_rule).agg(_agg).dropna(how="all")
                _df_chart = _df_resampled.tail(_period_arg) if _period_arg else _df_resampled
            st.plotly_chart(
                _main_chart(_df_chart, teto, ticker, T, cs=cs),
                use_container_width=True,
                config={"displayModeBar": False, "displaylogo": False},
            )
    except Exception as e:
        st.error(f"Chart error: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # 🧠 ANÁLISE ESTRUTURADA — unified narrative (trend + technicals + valuation)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="eg-nav-anchor" id="sec-inteligencia"></div>' + _ticker_chip_html, unsafe_allow_html=True)
    st.markdown(
        f'<div class="eg-section-header" style="margin-top:12px;">{T["narrative_title"]}</div>',
        unsafe_allow_html=True,
    )
    _narr_lines: list = []
    _price_str = f"{cs}{price:,.2f}"
    if cs == "R$":
        _price_str = f"{cs}{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Tendência geral (puxa do trend["overall"] traduzido)
    _trend_map_label = {
        "TENDÊNCIA DE ALTA FORTE":  T["trend_bull_strong"],
        "TENDÊNCIA DE ALTA":        T["trend_bull"],
        "TENDÊNCIA DE BAIXA FORTE": T["trend_bear_strong"],
        "TENDÊNCIA DE BAIXA":       T["trend_bear"],
    }
    _trend_label = _trend_map_label.get(trend.get("overall", ""), T["trend_neutral"])
    _narr_lines.append(T["narr_trend_overall"].format(trend=_trend_label))

    # Moving averages
    _ma20  = trend.get("ma20")
    _ma200 = trend.get("ma200")
    if _ma20:
        _ma20_str = f"{cs}{_ma20:,.2f}"
        if cs == "R$":
            _ma20_str = f"{cs}{_ma20:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if price >= _ma20:
            _narr_lines.append(T["narr_ma_above"].format(
                p=_price_str, d=20, ma=_ma20_str, dir=T["trend_bull"].lower()))
        else:
            _narr_lines.append(T["narr_ma_below"].format(
                p=_price_str, d=20, ma=_ma20_str, dir=T["trend_bear"].lower()))
    if _ma200:
        _ma200_str = f"{cs}{_ma200:,.2f}"
        if cs == "R$":
            _ma200_str = f"{cs}{_ma200:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if price >= _ma200:
            _narr_lines.append(T["narr_ma_above"].format(
                p=_price_str, d=200, ma=_ma200_str, dir=T["trend_bull"].lower()))
        else:
            _narr_lines.append(T["narr_ma_below"].format(
                p=_price_str, d=200, ma=_ma200_str, dir=T["trend_bear"].lower()))

    # P/L
    _pe = fundamentals.get("pe_ratio")
    if _pe and _pe > 0:
        if _pe < 10:
            _pe_hint = T["narr_pe_cheap"]
        elif _pe <= 20:
            _pe_hint = T["narr_pe_fair"]
        else:
            _pe_hint = T["narr_pe_rich"]
        _narr_lines.append(T["narr_pe"].format(pe=_pe, hint=_pe_hint))

    # P/VP
    _pb = fundamentals.get("pb_ratio")
    if _pb and _pb > 0:
        if _pb < 0.95:
            _narr_lines.append(T["narr_pb_discount"].format(
                pb=_pb, pct=(1 - _pb) * 100))
        elif _pb > 1.05:
            _narr_lines.append(T["narr_pb_premium"].format(
                pb=_pb, pct=(_pb - 1) * 100))
        else:
            _narr_lines.append(T["narr_pb_fair"].format(pb=_pb))

    # RSI
    if rsi_now < 30:
        _narr_lines.append(T["narr_rsi_oversold"].format(rsi=rsi_now))
    elif rsi_now > 70:
        _narr_lines.append(T["narr_rsi_overbought"].format(rsi=rsi_now))
    else:
        _narr_lines.append(T["narr_rsi_neutral"].format(rsi=rsi_now))

    # Solvência (não aplicável a bancos)
    if best_name == "Bancos":
        _narr_lines.append(T["narr_bank_note"])
    else:
        _ndx = health.get("debt_ebitda_value")
        if _ndx is not None:
            if _ndx <= 3:
                _narr_lines.append(T["narr_debt_healthy"].format(x=_ndx))
            else:
                _narr_lines.append(T["narr_debt_risk"].format(x=_ndx))

    st.markdown(
        "<div style='background:#161b22;border:1px solid #21262d;"
        "border-radius:10px;padding:14px 18px;font-size:.84rem;"
        "color:#e6edf3;line-height:1.55;'>"
        + "<br>".join(_md_to_html(l) for l in _narr_lines) +
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Dividends (historical bar chart) ──────────────────────────────────────
    st.markdown('<div class="eg-nav-anchor" id="sec-proventos"></div>' + _ticker_chip_html, unsafe_allow_html=True)
    st.markdown(f'<div class="eg-section-header">{T["dividends_title"]}</div>', unsafe_allow_html=True)
    if dividends is not None and not dividends.empty:
        st.plotly_chart(
            _dividend_chart(dividends, ticker, T, cs=cs),
            use_container_width=True,
            config={"displayModeBar": False, "displaylogo": False},
        )
        annual_d = dividends.resample("YE").sum()
        st.markdown(
            T["div_summary"].format(
                avg=avg_div, hi=float(annual_d.max()),
                lo=float(annual_d.min()), n=len(annual_d), cs=cs,
            ),
            unsafe_allow_html=True,
        )
    else:
        st.info(T["no_dividends"])

    st.divider()

    # ── Dividend Calendar ─────────────────────────────────────────────────────
    st.markdown(_ticker_chip_html + f'<div class="eg-section-header">{T["cal_title"]}</div>', unsafe_allow_html=True)
    _cal = get_dividend_calendar(ticker)
    if _cal.empty and dividends is not None and not dividends.empty:
        _today = pd.Timestamp.now().normalize()
        _rows = []
        for _ex_date, _val in dividends.tail(15).items():
            _ex_ts = pd.Timestamp(_ex_date).normalize()
            _com_ts = _ex_ts - pd.offsets.BDay(1)
            _status = "paid" if _ex_ts < _today else "provisioned"
            _d_until = int((_com_ts - _today).days) if _com_ts >= _today else None
            _rows.append({"type": "Div/JCP", "com_date": _com_ts, "ex_date": _ex_ts,
                          "payment_date": None, "value": float(_val),
                          "status": _status, "days_until_com": _d_until})
        if _rows:
            _cal = pd.DataFrame(_rows).sort_values("ex_date", ascending=False).reset_index(drop=True)
    if not _cal.empty:
        # Countdown banner for upcoming dividends
        _upcoming = _cal[_cal["status"] == "provisioned"]
        for _, _crow in _upcoming.iterrows():
            _d = _crow.get("days_until_com")
            if _d is not None and _d >= 0:
                st.markdown(
                    f"<div style='background:rgba(212,175,55,.10);border:1px solid #d4af37;"
                    f"border-radius:8px;padding:10px 16px;margin-bottom:8px;font-size:.88rem;'>"
                    f"{T['cal_countdown'].format(d=_d, v=_crow['value'], cs=cs)}</div>",
                    unsafe_allow_html=True,
                )
        # Formatted display table
        _cal_disp = pd.DataFrame({
            T["cal_type"]:     _cal["type"],
            T["cal_com_date"]: _cal["com_date"].dt.strftime("%d/%m/%Y"),
            T["cal_ex_date"]:  _cal["ex_date"].dt.strftime("%d/%m/%Y"),
            T["cal_payment"]:  _cal["payment_date"].apply(
                lambda x: x.strftime("%d/%m/%Y") if pd.notna(x) else "—"
            ),
            T["cal_value"].format(cs=cs): _cal["value"].apply(lambda x: f"{cs} {x:.4f}"),
            T["cal_status"]:   _cal["status"].map(
                {"paid": T["cal_paid"], "provisioned": T["cal_provisioned"]}
            ),
        })
        st.dataframe(_cal_disp, use_container_width=True, hide_index=True)
        st.caption(T["cal_com_hint"])
    else:
        st.info(T["cal_no_data"])

    # ── Glossary expander ─────────────────────────────────────────────────────
    st.markdown('<div class="eg-nav-anchor" id="sec-indicadores"></div>' + _ticker_chip_html, unsafe_allow_html=True)
    with st.expander(T["glossary_title"], expanded=True):
        _g1, _g2 = st.columns(2)
        _gitems = T["glossary_items"]
        _gmid   = len(_gitems) // 2 + len(_gitems) % 2
        # Escapa "$" para evitar modo LaTeX do markdown do Streamlit.
        with _g1:
            for _gterm, _gdesc in _gitems[:_gmid]:
                st.markdown(f"**{_gterm}** — {_gdesc}".replace("$", "\\$"))
        with _g2:
            for _gterm, _gdesc in _gitems[_gmid:]:
                st.markdown(f"**{_gterm}** — {_gdesc}".replace("$", "\\$"))

    # ── Footer / Disclaimer ───────────────────────────────────────────────────
    st.divider()
    st.markdown(
        f'<div class="eg-disclaimer">{T["disclaimer"]}</div>',
        unsafe_allow_html=True,
    )
    st.caption(T["data_source"].format(version=APP_VERSION))
    st.markdown(
        f"<div style='text-align:center;color:#6e7681;font-size:.72rem;margin-top:8px;'>"
        f"{T['footer_credit']}"
        f"</div>",
        unsafe_allow_html=True,
    )
    _footer_stats = get_stats()
    _visits_total = f"{_footer_stats['total']:,}"
    _visits_today = f"{_footer_stats['today']:,}"
    st.markdown(
        f"<div style='text-align:center;color:#484f58;font-size:.6rem;margin-top:4px;'>"
        f"{T['footer_visits'].format(total=_visits_total, today=_visits_today)}"
        f"</div>",
        unsafe_allow_html=True,
    )
    _render_feedback_box()
    _render_share_buttons(T)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    _inject_css()

    # ── Session defaults ─────────────────────────────────────────────────────
    if "lang" not in st.session_state:
        st.session_state.lang = "pt"
    if "user" not in st.session_state or st.session_state.user is None:
        # Apple Store model: skip login gate, bootstrap an anonymous user
        st.session_state.user = _make_anon_user()

    T    = get_translator()

    # ── Google Analytics (injeta no parent DOM para garantir execução) ────────
    if "ga_injected" not in st.session_state:
        import streamlit.components.v1 as _ga_comp
        _ga_comp.html("""
        <script>
        (function() {
            var doc = window.parent.document;
            if (doc.getElementById('eg-ga-script')) return;
            var s1 = doc.createElement('script');
            s1.id = 'eg-ga-script';
            s1.async = true;
            s1.src = 'https://www.googletagmanager.com/gtag/js?id=G-BBKMK9TL6P';
            doc.head.appendChild(s1);
            var s2 = doc.createElement('script');
            s2.textContent = "window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-BBKMK9TL6P');";
            doc.head.appendChild(s2);
        })();
        </script>
        """, height=0)
        st.session_state.ga_injected = True

    # ── FAB — botão flutuante que abre/fecha sidebar no mobile ─────────────
    import streamlit.components.v1 as _components
    _components.html(f"""
    <script>
    (function() {{
        var doc = window.parent.document;
        // Inject the FAB directly into the parent document
        if (doc.getElementById('eg-fab-injected')) return;
        var fab = doc.createElement('div');
        fab.id = 'eg-fab-injected';
        fab.innerHTML = '\u2630';
        fab.style.cssText = 'display:none;position:fixed;bottom:16px;left:16px;z-index:999999;'
            + 'background:linear-gradient(135deg,#b8941f,#d4af37);color:#0d1117;'
            + 'border-radius:50%;width:48px;height:48px;font-size:20px;font-weight:900;'
            + 'box-shadow:0 4px 16px rgba(212,175,55,.5);'
            + 'cursor:pointer;font-family:Inter,system-ui,sans-serif;'
            + 'display:flex;align-items:center;justify-content:center;';
        fab.onclick = function() {{
            var openBtn = doc.querySelector('[data-testid="collapsedControl"]');
            var closeBtn = doc.querySelector('[data-testid="stSidebarCollapseButton"] button');
            if (openBtn) openBtn.click();
            else if (closeBtn) closeBtn.click();
        }};
        doc.body.appendChild(fab);
        // Show only on mobile
        function checkWidth() {{
            fab.style.display = window.parent.innerWidth <= 768 ? 'block' : 'none';
        }}
        checkWidth();
        window.parent.addEventListener('resize', checkWidth);
    }})();
    </script>
    """, height=0)
    user = st.session_state.user

    # ── Analytics — registrar visita (1x por sessão) ─────────────────────────
    if "visit_registered" not in st.session_state:
        _stats = register_visit()
        st.session_state.visit_registered = True
        st.session_state.visit_stats = _stats
    else:
        _stats = st.session_state.get("visit_stats") or get_stats()

    # ── Top-right auth strip + optional inline login form ────────────────────
    _render_top_auth_bar(user, T)
    _render_inline_login(T)

    # ── 🔔 Pension data alert (after the 15th, once per data_base) ───────────
    _maybe_pension_alert(T)

    # ── App header ───────────────────────────────────────────────────────────
    st.markdown(
        "<h1 style='font-size:1.7rem;font-weight:900;letter-spacing:-.5px;margin-bottom:0;'>"
        "<span style='color:#d4af37;'>EQUITY</span>"
        "<span style='color:#e6edf3;'> GUARD</span>"
        "<span class='eg-beta-badge'>BETA</span>"
        "</h1>"
        "<div class='eg-beta-notice'>"
        "⚠️ Site em desenvolvimento &middot; versão beta &middot; dados e funcionalidades podem mudar sem aviso. "
        "Envie sugestões pela caixa de feedback no rodapé."
        "</div>",
        unsafe_allow_html=True,
    )
    _render_share_buttons(T)

    # ── Navigation menu (topo da página, logo após o header) ────────────────
    _nav_items = [
        (T["nav_cotacao"], "sec-cotacao"),
        (T["nav_projecao"], "sec-projecao"),
        (T["nav_dividendos"], "sec-dividendos"),
        (T["nav_metricas"], "sec-metricas"),
        (T["nav_saude"], "sec-saude"),
        (T["nav_tecnico"], "sec-tecnico"),
        (T["nav_inteligencia"], "sec-inteligencia"),
        (T["nav_proventos"], "sec-proventos"),
        (T["nav_indicadores"], "sec-indicadores"),
    ]
    _nav_btns_html = "".join(
        f'<button class="eg-nav-btn" data-target="{aid}">{label}</button>'
        for label, aid in _nav_items
    )

    import streamlit.components.v1 as _nav_comp
    _nav_comp.html(f"""
    <style>
    .eg-nav-menu {{
        background: #1c2333; border: 1px solid #d4af37;
        border-radius: 12px; padding: 8px 12px; display: flex; gap: 4px;
        overflow-x: auto; -webkit-overflow-scrolling: touch;
        scrollbar-width: none; justify-content: center; flex-wrap: wrap;
    }}
    .eg-nav-menu::-webkit-scrollbar {{ display: none; }}
    .eg-nav-btn {{
        background: rgba(212,175,55,0.06); color: #e6edf3;
        border: 1px solid #30363d; border-radius: 20px;
        padding: 6px 14px; font-size: 0.78rem; font-weight: 600;
        white-space: nowrap; cursor: pointer;
        transition: all 0.2s; font-family: 'Inter', system-ui, sans-serif;
    }}
    .eg-nav-btn:hover {{ color: #0d1117; border-color: #d4af37; background: #d4af37; }}
    .eg-nav-topo {{ color: #d4af37; border-color: #d4af37; margin-left: auto; }}
    </style>
    <div class="eg-nav-menu">
        {_nav_btns_html}
        <button class="eg-nav-btn eg-nav-topo" data-target="__top__">{T["nav_topo"]}</button>
    </div>
    <script>
    document.querySelectorAll('.eg-nav-btn').forEach(function(btn) {{
        btn.addEventListener('click', function() {{
            var aid = btn.getAttribute('data-target');
            if (aid === '__top__') {{
                window.parent.document.querySelector('section.main').scrollTo({{top:0,behavior:'smooth'}});
                return;
            }}
            var el = window.parent.document.getElementById(aid);
            if (el) el.scrollIntoView({{behavior:'smooth', block:'start'}});
        }});
    }});
    </script>
    """, height=52)

    # ── 🗞️ Briefing de Fechamento (expander aberto por default) ────────────
    _render_briefing(T)

    # ── Sidebar + analysis ───────────────────────────────────────────────────
    ticker, period, target_yield, clicked = render_sidebar(user, T)

    if not ticker:
        st.info("👈 " + T["analyze_btn"])
        return

    render_analysis(user, ticker, period, target_yield, clicked, T)


if __name__ == "__main__":
    main()
