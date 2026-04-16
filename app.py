"""
app.py — Equity Guard  v2.0
Premium B3 stock analyzer · Dark mode · i18n PT/EN/ES
Login por e-mail · Créditos · Mercado Pago Pix (UI shell)
"""

import math
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
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
    </head>""",
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
/* Section header */
.eg-section-header { font-size:.72rem; font-weight:700; letter-spacing:1.8px; text-transform:uppercase; color:#8b949e; margin:1.2rem 0 .6rem; }
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
    /* Let plotly charts breathe */
    [data-testid="stPlotlyChart"] { overflow: hidden; }
    /* Top auth bar: stack buttons full-width on mobile */
    [data-testid="stHorizontalBlock"] [data-testid="column"] .stButton > button {
        font-size: .82rem !important;
    }
}
/* All widths: ensure tables never break layout horizontally */
[data-testid="stDataFrame"] > div { overflow-x: auto !important; }
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
        increasing=dict(line=dict(color="#3fb950"), fillcolor="#3fb950"),
        decreasing=dict(line=dict(color="#f85149"), fillcolor="#f85149"),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df_ma.index, y=df_ma["MA20"], name="MA20",
        line=dict(color="#e3b341", width=1.6),
        hovertemplate=f"MA20: {cs} %{{y:.2f}}<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df_ma.index, y=df_ma["MA200"], name="MA200",
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
                marker=dict(color="#f85149", size=7, symbol="triangle-down"),
                hovertemplate=f"{T['top_marker']}: {cs} %{{y:.2f}}<extra></extra>",
            ), row=1, col=1)
        if not bottoms.empty:
            fig.add_trace(go.Scatter(
                x=bottoms.index, y=bottoms.values, mode="markers", name=T["bottom_marker"],
                marker=dict(color="#3fb950", size=7, symbol="triangle-up"),
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

    fig.update_layout(height=680, hovermode="x unified", xaxis_rangeslider_visible=False, **_CHART_LAYOUT)
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


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_quick_history(ticker: str, period: str) -> Optional[pd.DataFrame]:
    """Cached wrapper for the interactive period chart (5-min TTL)."""
    return get_stock_history(ticker, period)


@st.cache_data(ttl=600, show_spinner=False)
def _fetch_fx_usdbrl() -> Optional[dict]:
    """Cached wrapper for the USDBRL macro panel (10-min TTL)."""
    return get_fx_usdbrl()


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
    Fires a one-time toast after the 15th of the month notifying the user
    that new PrevDow / Nitro Prev returns may be available.
    Uses session_state to avoid spamming on every rerun. Resets when the
    PREVDOW_DATA["data_base"] string changes (i.e., next month's update).
    """
    today = pd.Timestamp.now()
    if today.day < 15:
        return
    ref      = PREVDOW_DATA.get("data_base", "")
    seen_key = f"_pension_seen_{ref}"
    if not ref or st.session_state.get(seen_key):
        return
    try:
        st.toast(
            T["pension_alert_toast"].format(ref=ref),
            icon="🏦",
        )
    except Exception:
        pass  # st.toast may not be available on very old Streamlit
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
        color = "#3fb950" if chg > 0 else ("#f85149" if chg < 0 else "#8b949e")
        return f"<span style='color:{color};font-weight:700;'>{arrow}{chg:+.2f}%</span>"

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

    today = pd.Timestamp.now().strftime("%d/%m/%Y")
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
                f"🏦 Juros</div>"
                f"{_card(_fed_label, f'{FED_FUNDS_RATE:.2f}% {_aa}', '')}"
                f"{_card(_selic_label, f'{SELIC_RATE:.2f}% {_aa}', '')}"
                f"<div style='height:8px;'></div>"
                f"<div style='font-size:.78rem;color:#d4af37;font-weight:700;"
                f"text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;'>"
                f"🛢️ Commodities</div>"
                f"{_card('Brent', f'US$ {brent_val}', _fmt_chg('Brent'))}"
                f"{_card('WTI', f'US$ {wti_val}', _fmt_chg('WTI'))}"
                f"</div>",
                unsafe_allow_html=True,
            )

        with _bc2:
            st.markdown(
                f"<div style='background:#161b22;border:1px solid #30363d;"
                f"border-radius:10px;padding:14px 16px;'>"
                f"<div style='font-size:.78rem;color:#d4af37;font-weight:700;"
                f"text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;'>"
                f"📊 Bolsas</div>"
                f"{_card('Ibovespa', _fmt_val('IBOV', 'br'), _fmt_chg('IBOV'))}"
                f"{_card('S&P 500', _fmt_val('S&P 500'), _fmt_chg('S&P 500'))}"
                f"{_card('NASDAQ', _fmt_val('NASDAQ'), _fmt_chg('NASDAQ'))}"
                f"{_card('FTSE', _fmt_val('FTSE'), _fmt_chg('FTSE'))}"
                f"</div>",
                unsafe_allow_html=True,
            )

        # ── WhatsApp share ───────────────────────────────────────────────────
        wa_lines = [
            f"🗞️ *Briefing Equity Guard · {today}*", "",
            f"📊 *Bolsas*",
            f"Ibovespa {_fmt_val('IBOV', 'br')} · S&P 500 {_fmt_val('S&P 500')} · NASDAQ {_fmt_val('NASDAQ')} · FTSE {_fmt_val('FTSE')}",
            "",
            f"🛢️ *Commodities*",
            f"Brent US$ {_fmt_val('Brent')} · WTI US$ {_fmt_val('WTI')}",
            "",
            f"🏦 *Juros*",
            f"Selic {SELIC_RATE:.2f}% (COPOM {_fmt_date_br(SELIC_NEXT_MEETING)}) · Fed {FED_FUNDS_RATE:.2f}% (FOMC {_fmt_date_br(FED_NEXT_MEETING)})",
            "",
            "_Enviado via Equity Guard_",
        ]
        wa_url = f"https://wa.me/?text={_url.quote(chr(10).join(wa_lines))}"
        try:
            st.link_button(
                T["briefing_copy_btn"], wa_url,
                use_container_width=True, type="primary",
            )
        except Exception:
            st.markdown(
                f"<a href='{wa_url}' target='_blank' style='display:block;"
                f"text-align:center;background:#25d366;color:#fff;"
                f"padding:8px;border-radius:8px;font-size:.82rem;"
                f"font-weight:700;text-decoration:none;margin-top:6px;'>"
                f"{T['briefing_copy_btn']}</a>",
                unsafe_allow_html=True,
            )
        st.markdown(
            "<div style='font-size:.58rem;color:#484f58;text-align:right;margin-top:4px;'>"
            "Fonte: Yahoo Finance · BCB · Fed</div>",
            unsafe_allow_html=True,
        )


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
            color   = "#3fb950" if chg > 0 else ("#f85149" if chg < 0 else "#8b949e")
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
    Branded sidebar card (vermelho/branco) with monthly and YTD returns for
    CDI and Balanced profiles, plus a link to the official rentabilidade
    portal and a WhatsApp share button. Values come from config.PREVDOW_DATA
    and are meant to be updated manually once a month.
    """
    import urllib.parse as _url
    d = PREVDOW_DATA

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
    def _val_html(v: float) -> str:
        c = "#3fb950" if v > 0 else ("#f85149" if v < 0 else "#8b949e")
        return f"<span style='font-weight:800;color:{c};'>{v:+.2f}%</span>"

    _hdr = "color:#6e7681;font-size:.68rem;font-weight:600;text-transform:uppercase;letter-spacing:.3px;"
    _cell = "padding:6px 0;font-size:.82rem;"
    st.markdown(
        "<div style='background:#161b22;border:1px solid #c0392b;"
        "border-top:none;border-radius:0 0 10px 10px;padding:8px 14px 10px;'>"
        "<table style='width:100%;border-collapse:collapse;'>"
        f"<tr style='border-bottom:1px solid #30363d;'>"
        f"<td style='{_hdr}padding-bottom:6px;'>Perfil</td>"
        f"<td style='{_hdr}padding-bottom:6px;text-align:right;'>{T['prevdow_month']}</td>"
        f"<td style='{_hdr}padding-bottom:6px;text-align:right;'>{T['prevdow_year']}</td>"
        f"</tr>"
        f"<tr style='border-bottom:1px dashed #21262d;'>"
        f"<td style='{_cell}color:#e6edf3;font-weight:600;'>{T['prevdow_cdi_label']}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d['cdi_month'])}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d['cdi_year'])}</td>"
        f"</tr>"
        f"<tr>"
        f"<td style='{_cell}color:#e6edf3;font-weight:600;'>{T['prevdow_balanced_label']}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d['balanced_month'])}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d['balanced_year'])}</td>"
        f"</tr>"
        "</table></div>",
        unsafe_allow_html=True,
    )

    # ── External link (portal oficial) ────────────────────────────────────────
    try:
        st.link_button(
            T["prevdow_link"], d["url"],
            use_container_width=True, type="secondary",
        )
    except Exception:
        # Fallback: markdown link styled as button (older Streamlit)
        st.markdown(
            f"<a href='{d['url']}' target='_blank' style='display:block;"
            f"text-align:center;background:#c0392b;color:#fff;"
            f"padding:8px;border-radius:8px;font-size:.78rem;"
            f"font-weight:700;text-decoration:none;margin-top:6px;'>"
            f"{T['prevdow_link']}</a>",
            unsafe_allow_html=True,
        )

    # ── WhatsApp share (deep link with pre-filled message) ────────────────────
    _wa_text = T["prevdow_share_text"].format(
        ref=d["data_base"],
        cdi_m=d["cdi_month"], cdi_y=d["cdi_year"],
        bal_m=d["balanced_month"], bal_y=d["balanced_year"],
    ).replace("\\n", "\n")
    _wa_url = f"https://wa.me/?text={_url.quote(_wa_text)}"
    try:
        st.link_button(
            T["prevdow_share"], _wa_url,
            use_container_width=True, type="primary",
        )
    except Exception:
        st.markdown(
            f"<a href='{_wa_url}' target='_blank' style='display:block;"
            f"text-align:center;background:#25d366;color:#fff;"
            f"padding:8px;border-radius:8px;font-size:.78rem;"
            f"font-weight:700;text-decoration:none;margin-top:6px;'>"
            f"{T['prevdow_share']}</a>",
            unsafe_allow_html=True,
        )

    st.markdown(
        "<div style='font-size:.58rem;color:#484f58;text-align:right;margin-top:2px;'>"
        "Fonte: Portal Prevdow</div>",
        unsafe_allow_html=True,
    )


def _render_nitro_panel(T: dict) -> None:
    """
    Nitro Prev (IFM Previdência / Votorantim).
    Branded sidebar card (azul marinho + dourado) with monthly and YTD
    returns for CDI and Balanced profiles, plus a direct login link to the
    official participant portal. Values come from config.NITRO_DATA and are
    meant to be updated manually once a month.
    """
    d = NITRO_DATA
    NAVY = "#003366"
    NAVY_HI = "#004488"
    GOLD = "#FFCC00"

    # ── Branded header (navy gradient, gold text) ─────────────────────────────
    st.markdown(
        f"<div style='background:linear-gradient(135deg,{NAVY},{NAVY_HI});"
        f"border-radius:10px 10px 0 0;padding:10px 14px;margin-top:14px;"
        f"border:1px solid {NAVY};border-bottom:none;'>"
        f"<div style='display:flex;align-items:center;justify-content:space-between;'>"
        f"<span style='font-size:.88rem;font-weight:800;color:{GOLD};"
        f"letter-spacing:.3px;'>{T['nitro_title']}</span>"
        f"<span style='font-size:.68rem;color:rgba(255,204,0,.85);'>"
        f"{T['prevdow_subtitle'].format(ref=d['data_base'])}</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # ── Returns table (Perfil | No mês | No ano) ──────────────────────────────
    def _val_html(v: float) -> str:
        c = "#3fb950" if v > 0 else ("#f85149" if v < 0 else "#8b949e")
        return f"<span style='font-weight:800;color:{c};'>{v:+.2f}%</span>"

    _hdr = "color:#6e7681;font-size:.68rem;font-weight:600;text-transform:uppercase;letter-spacing:.3px;"
    _cell = "padding:6px 0;font-size:.82rem;"
    st.markdown(
        f"<div style='background:#161b22;border:1px solid {NAVY};"
        f"border-top:none;border-radius:0 0 10px 10px;padding:8px 14px 10px;'>"
        "<table style='width:100%;border-collapse:collapse;'>"
        f"<tr style='border-bottom:1px solid #30363d;'>"
        f"<td style='{_hdr}padding-bottom:6px;'>Perfil</td>"
        f"<td style='{_hdr}padding-bottom:6px;text-align:right;'>{T['prevdow_month']}</td>"
        f"<td style='{_hdr}padding-bottom:6px;text-align:right;'>{T['prevdow_year']}</td>"
        f"</tr>"
        f"<tr style='border-bottom:1px dashed #21262d;'>"
        f"<td style='{_cell}color:#e6edf3;font-weight:600;'>{T['prevdow_cdi_label']}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d['cdi_month'])}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d['cdi_year'])}</td>"
        f"</tr>"
        f"<tr>"
        f"<td style='{_cell}color:#e6edf3;font-weight:600;'>{T['prevdow_balanced_label']}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d['balanced_month'])}</td>"
        f"<td style='{_cell}text-align:right;'>{_val_html(d['balanced_year'])}</td>"
        f"</tr>"
        "</table></div>",
        unsafe_allow_html=True,
    )

    # ── Login button — navy bg + gold text (custom HTML to enforce branding) ─
    st.markdown(
        f"<a href='{d['url']}' target='_blank' style='display:block;"
        f"text-align:center;background:{NAVY};color:{GOLD};"
        f"padding:10px 8px;border-radius:8px;font-size:.78rem;"
        f"font-weight:800;text-decoration:none;margin-top:6px;"
        f"border:1px solid {GOLD};letter-spacing:.3px;'>"
        f"{T['nitro_link']}</a>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='font-size:.58rem;color:#484f58;text-align:right;margin-top:2px;'>"
        "Fonte: IFM Previdência</div>",
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

    bid    = fx.get("bid", 0)
    ask    = fx.get("ask", 0)
    avg    = fx.get("avg", 0)
    change = fx["change"]
    series = fx.get("series")
    fetched = fx.get("fetched_at")

    def _fx_fmt(v):
        return f"R${v:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")

    arrow = "▲" if change > 0 else ("▼" if change < 0 else "■")
    color = "#3fb950" if change > 0 else ("#f85149" if change < 0 else "#8b949e")

    ts_html = ""
    if fetched is not None:
        _ts = T["macro_updated_at"].format(
            date=fetched.strftime("%d/%m"),
            time=fetched.strftime("%H:%M"),
        )
        ts_html = (
            f"<div style='font-size:.66rem;color:#6e7681;margin-top:6px;'>"
            f"🕒 {_ts}</div>"
        )

    _row_style = "display:flex;justify-content:space-between;align-items:baseline;padding:3px 0;"
    st.markdown(
        f"<div style='background:#161b22;border:1px solid #21262d;"
        f"border-radius:10px;padding:10px 12px;margin-top:2px;'>"
        f"<div style='font-size:.7rem;color:#6e7681;margin-bottom:4px;'>"
        f"{T['macro_usdbrl_label']}</div>"
        f"<div style='{_row_style}border-bottom:1px solid #21262d;'>"
        f"<span style='font-size:.75rem;color:#8b949e;'>Compra</span>"
        f"<span style='font-size:.95rem;font-weight:700;color:#e6edf3;'>{_fx_fmt(bid)}</span></div>"
        f"<div style='{_row_style}border-bottom:1px solid #21262d;'>"
        f"<span style='font-size:.75rem;color:#8b949e;'>Venda</span>"
        f"<span style='font-size:.95rem;font-weight:700;color:#e6edf3;'>{_fx_fmt(ask)}</span></div>"
        f"<div style='{_row_style}'>"
        f"<span style='font-size:.75rem;color:#d4af37;font-weight:600;'>Médio</span>"
        f"<span style='font-size:.95rem;font-weight:700;color:#d4af37;'>{_fx_fmt(avg)}</span></div>"
        f"<div style='text-align:right;margin-top:4px;'>"
        f"<span style='font-size:.78rem;font-weight:700;color:{color};'>"
        f"{arrow} {change:+.2f}%</span></div>"
        f"{ts_html}</div>",
        unsafe_allow_html=True,
    )

    # Gráfico dólar venda (7 dias)
    if series is not None and len(series) >= 2:
        try:
            spark = go.Figure()
            spark.add_trace(go.Scatter(
                x=list(series.index), y=list(series.values),
                mode="lines",
                line=dict(color=color, width=1.8, shape="spline", smoothing=.5),
                fill="tozeroy",
                fillcolor=("rgba(63,185,80,.12)" if change >= 0 else "rgba(248,81,73,.12)"),
                hovertemplate="%{x|%d %b}<br>R$ %{y:.4f}<extra></extra>",
            ))
            y_min = float(series.min())
            y_max = float(series.max())
            pad = (y_max - y_min) * 0.15 if y_max > y_min else 0.05
            spark.update_layout(
                height=90,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=2, b=14),
                showlegend=False,
                xaxis=dict(
                    visible=True, showgrid=False, zeroline=False, showline=False,
                    tickfont=dict(color="#6e7681", size=8),
                    tickformat="%d/%m", nticks=3,
                ),
                yaxis=dict(visible=False, range=[y_min - pad, y_max + pad]),
                hovermode="x unified",
            )
            st.caption("Dólar venda · 7 dias")
            st.plotly_chart(spark, use_container_width=True,
                            config={"displayModeBar": False})
        except Exception:
            pass
    st.markdown(
        "<div style='font-size:.58rem;color:#484f58;text-align:right;margin-top:2px;'>"
        "Fonte: BCB PTAX · Yahoo Finance</div>",
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
        (T["day_high"],    _today_high,  "#3fb950"),
        (T["day_low"],     _today_low,   "#f85149"),
        (T["range_low"],   _w52_lo,      "#f85149"),
        (T["range_high"],  _w52_hi,      "#3fb950"),
    ]
    _oc = st.columns(6)
    for _col, (_lbl, _val, _vc) in zip(_oc, _ohlc_items):
        _vstr = _fmt_money(_val, cs) if _val is not None else "—"
        with _col:
            st.markdown(
                f"<div style='background:#161b22;border:1px solid #21262d;"
                f"border-radius:9px;padding:10px 8px;text-align:center;'>"
                f"<div style='font-size:.7rem;color:#6e7681;margin-bottom:4px;'>{_lbl}</div>"
                f"<div style='font-size:.95rem;font-weight:700;color:{_vc};'>{_vstr}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


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

    line_c = "#3fb950" if is_up else "#f85149"
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
    colors = ["#3fb950" if v >= avg else "#e3b341" for v in annual.values]
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
            bar_c = "#3fb950" if pct > 50 else ("#e3b341" if pct > 20 else "#f85149")
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

        st.divider()

        # ══════════════════════════════════════════════════════════════════════
        # 1. MACRO PANEL — USD/BRL (logo após Cadastre-se)
        # ══════════════════════════════════════════════════════════════════════
        _render_macro_panel(T)

        # ══════════════════════════════════════════════════════════════════════
        # 2. HUB DE PREVIDÊNCIA — Prevdow + Nitro Prev (IFM)
        # ══════════════════════════════════════════════════════════════════════
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
            "strong_buy": "#3fb950",
            "buy":        "#56d364",
            "wait":       "#d29922",
            "neutral":    "#58a6ff",
            "avoid":      "#f85149",
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
        bg, vc, border = "rgba(63,185,80,.08)", "#3fb950", "rgba(63,185,80,.25)"
    elif ok is False:
        bg, vc, border = "rgba(248,81,73,.08)", "#f85149", "rgba(248,81,73,.25)"
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
                f"<h3 style='margin-bottom:2px;'>{name} &nbsp;"
                f"<code style='font-size:.75rem;background:#161b22;padding:3px 8px;"
                f"border-radius:6px;border:1px solid #30363d;'>{normalize_ticker(ticker)}</code>"
                f"&nbsp;{best_badge}{dev_badge}</h3>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<span style='color:#8b949e;font-size:.84rem;'>"
                f"{fundamentals.get('sector','—')} › {fundamentals.get('industry','—')}"
                f"</span>",
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

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # 📈 INTERACTIVE QUOTE — right below the signal (primary scroll experience)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="eg-nav-anchor" id="sec-cotacao"></div>', unsafe_allow_html=True)
    _render_interactive_quote(ticker, df, T, cs)

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # 🔮 FUTURE-FOCUS BLOCK — projection + monthly map at the top of the page
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="eg-nav-anchor" id="sec-projecao"></div>', unsafe_allow_html=True)
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
            f'<div class="eg-section-header">{T["month_map_title"]}</div>',
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
                _ring = "box-shadow:0 0 0 2px #3fb950;" if _is_now else ""
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
    st.markdown('<div class="eg-nav-anchor" id="sec-dividendos"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="eg-section-header">{T["goal_title"]}</div>',
        unsafe_allow_html=True,
    )
    if avg_div > 0 and price and price > 0:
        _g1, _g2, _g3 = st.columns([2, 2, 3])
        with _g1:
            _goal_raw = st.number_input(
                f"{T['goal_input_label']} ({cs})",
                min_value=0.0, value=1000.0, step=100.0,
                key="goal_target", format="%.2f",
                label_visibility="collapsed",
            )
            _lang = st.session_state.get("lang", "pt")
            if _lang in ("pt", "es"):
                _goal_display = f"{cs}{_goal_raw:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                _goal_display = f"{cs}{_goal_raw:,.2f}"
            st.markdown(
                f"<div style='background:#161b22;border:1px solid #30363d;border-radius:8px;"
                f"padding:10px 14px;text-align:right;font-size:1rem;font-weight:700;"
                f"color:#e6edf3;margin-top:-10px;'>{_goal_display}</div>",
                unsafe_allow_html=True,
            )
            _goal_target = _goal_raw
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
                f"border-radius:10px;padding:14px 18px;margin-top:24px;font-size:.9rem;"
                f"color:#e6edf3;line-height:1.55;text-align:right;'>"
                f"{T['goal_result'].format(shares=_fmt_int(_shares_lot, cs), money=_fmt_money(_invest_total, cs))}"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info(T["goal_no_data"])

    st.divider()

    # ── Key metrics ───────────────────────────────────────────────────────────
    st.markdown('<div class="eg-nav-anchor" id="sec-metricas"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="eg-section-header">{T["current_price"][:2]} Métricas</div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.metric(T["current_price"], f"{cs} {price:.2f}", help=T["tooltip_price"])
    with m2:
        ceiling_label = T["ceiling_price"].format(pct=yield_pct)
        st.metric(ceiling_label, f"{cs} {teto:.2f}" if teto > 0 else T["na"], help=T["tooltip_ceiling"])
    with m3:
        if teto > 0:
            delta_txt = T["below_delta"] if margin > 0 else T["above_delta"]
            st.metric(T["safety_margin"], f"{margin:.1f}%",
                      delta=delta_txt, delta_color="normal" if margin > 0 else "inverse",
                      help=T["tooltip_margin"])
        else:
            st.metric(T["safety_margin"], T["na"], help=T["tooltip_margin"])
    with m4:
        dy = fundamentals.get("dividend_yield")
        st.metric(T["dividend_yield"], f"{dy*100:.2f}%" if dy else T["na"], help=T["tooltip_dy"])
    with m5:
        rsi_lbl = T["overbought"] if rsi_now > 70 else (T["oversold"] if rsi_now < 30 else T["neutral_rsi"])
        st.metric(T["rsi_label"], f"{rsi_now:.1f}", delta=rsi_lbl,
                  delta_color="inverse" if rsi_now > 70 else ("normal" if rsi_now < 30 else "off"),
                  help=T["tooltip_rsi"])

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
    st.markdown(f'<div class="eg-section-header">{T["perf_title"]}</div>', unsafe_allow_html=True)
    _perf = get_price_performance(df)
    if _perf:
        _pp1, _pp2, _pp3, _pp4, _pp5 = st.columns(5)
        for _col, _lbl, _ref, _chg in [
            (_pp1, T["perf_1d"],      _perf.get("yesterday"),  _perf.get("chg_1d")),
            (_pp2, T["perf_7d"],      _perf.get("price_7d"),   _perf.get("chg_7d")),
            (_pp3, T["perf_30d"],     _perf.get("price_30d"),  _perf.get("chg_30d")),
            (_pp4, T["perf_52w_min"], _perf.get("w52_min"),    None),
            (_pp5, T["perf_52w_max"], _perf.get("w52_max"),    None),
        ]:
            _clr   = "#3fb950" if (_chg is not None and _chg > 0) else (
                     "#f85149" if (_chg is not None and _chg < 0) else "#8b949e")
            _chg_s = f"{_chg:+.1f}%" if _chg is not None else "—"
            _ref_s = f"{cs} {_ref:.2f}" if _ref is not None else "—"
            with _col:
                st.markdown(
                    f"<div style='background:#161b22;border:1px solid #21262d;"
                    f"border-radius:10px;padding:10px 12px;text-align:center;'>"
                    f"<div style='font-size:.74rem;color:#6e7681;margin-bottom:3px;'>{_lbl}</div>"
                    f"<div style='font-size:1rem;font-weight:700;color:#e6edf3;'>{_ref_s}</div>"
                    f"<div style='font-size:.84rem;font-weight:700;color:{_clr};'>{_chg_s}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
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
            st.markdown(
                f"<div style='margin-top:14px;background:#161b22;border:1px solid #21262d;"
                f"border-radius:10px;padding:14px 20px;'>"
                f"<div style='font-size:.78rem;color:#d4af37;font-weight:700;"
                f"text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;'>"
                f"{T['range_52w_title']}</div>"
                f"<div style='display:flex;justify-content:space-between;align-items:flex-end;"
                f"font-size:.74rem;color:#6e7681;margin-bottom:6px;'>"
                f"<span>📉 {T['range_low']}<br>"
                f"<b style='color:#f85149;font-size:.95rem;'>{cs} {_w52_min:.2f}</b></span>"
                f"<span style='text-align:center;'>💎 {T['current_price'][2:].strip()}<br>"
                f"<b style='color:#d4af37;font-size:1.05rem;'>{cs} {_curr:.2f}</b></span>"
                f"<span style='text-align:right;'>📈 {T['range_high']}<br>"
                f"<b style='color:#3fb950;font-size:.95rem;'>{cs} {_w52_max:.2f}</b></span>"
                f"</div>"
                f"<div style='position:relative;height:12px;background:linear-gradient(90deg,"
                f"#3fb950 0%,#e3b341 50%,#f85149 100%);border-radius:6px;margin-top:10px;'>"
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
    st.markdown('<div class="eg-nav-anchor" id="sec-saude"></div>', unsafe_allow_html=True)
    col_h, col_t = st.columns(2)

    with col_h:
        st.markdown(f'<div class="eg-section-header">{T["health_title"]}</div>', unsafe_allow_html=True)

        pv = health["payout_value"]
        st.metric(
            f"📤 {T['payout']}",
            f"{pv:.1f}%" if pv is not None else T["na"],
            delta=T["payout_hint"], delta_color="off",
            help=T["tooltip_payout"],
        )

        dv = health["debt_ebitda_value"]
        if best_name == "Bancos" and dv is None:
            st.metric(
                f"🏦 {T['debt_ebitda']}",
                T["na"],
                help=T["tooltip_debt"],
            )
            st.caption(T["bank_ebitda_note"])
        else:
            st.metric(
                f"🏦 {T['debt_ebitda']}",
                f"{dv:.2f}×" if dv is not None else T["na"],
                delta=T["debt_ebitda_hint"], delta_color="off",
                help=T["tooltip_debt"],
            )

        rv = health["roe_value"]
        st.metric(
            f"📊 {T['roe']}",
            f"{rv:.1f}%" if rv is not None else T["na"],
            delta=T["roe_hint"], delta_color="off",
            help=T["tooltip_roe"],
        )

        pe = fundamentals.get("pe_ratio")
        if pe:
            st.metric(f"🔢 {T['pe_label']}", f"{pe:.1f}×", help=T["tooltip_pe"])
        pb = fundamentals.get("pb_ratio")
        if pb:
            st.metric(f"📚 {T['pb_label']}", f"{pb:.2f}×", help=T["tooltip_pb"])

    with col_t:
        st.markdown(f'<div class="eg-section-header">{T["trend_title"]}</div>', unsafe_allow_html=True)
        ov = trend["overall"]
        trend_map = {
            "TENDÊNCIA DE ALTA FORTE":  (T["trend_bull_strong"], "rgba(63,185,80,.12)",   "#3fb950"),
            "TENDÊNCIA DE ALTA":        (T["trend_bull"],        "rgba(63,185,80,.07)",   "#56d364"),
            "TENDÊNCIA DE BAIXA FORTE": (T["trend_bear_strong"], "rgba(248,81,73,.12)",   "#f85149"),
            "TENDÊNCIA DE BAIXA":       (T["trend_bear"],        "rgba(248,81,73,.07)",   "#ff6b6b"),
        }
        t_label, t_bg, t_color = trend_map.get(ov, (T["trend_neutral"], "#161b22", "#8b949e"))
        st.markdown(
            f"<div class='eg-trend-box' style='background:{t_bg};color:{t_color};'>{t_label}</div>",
            unsafe_allow_html=True,
        )
        _ma_cols = st.columns(2)
        for _i, (ma_val, ma_lbl) in enumerate([
            (trend.get("ma20"),  "MA20"),
            (trend.get("ma200"), "MA200"),
        ]):
            if ma_val:
                diff    = ((price - ma_val) / ma_val) * 100
                _ma_tip = T["tooltip_ma20"] if ma_lbl == "MA20" else T["tooltip_ma200"]
                with _ma_cols[_i]:
                    st.metric(
                        ma_lbl,
                        f"{cs} {ma_val:.2f}",
                        delta=f"{diff:+.1f}%",
                        delta_color="normal" if diff > 0 else "inverse",
                        help=_ma_tip,
                    )
        if trend.get("golden_cross"):
            st.success(T["golden_cross"])
        elif trend.get("death_cross"):
            st.error(T["death_cross"])

        rsi_bar_c = "#f85149" if rsi_now > 70 else ("#3fb950" if rsi_now < 30 else "#e3b341")
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
    st.markdown('<div class="eg-nav-anchor" id="sec-tecnico"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="eg-section-header">{T["chart_title"]}</div>', unsafe_allow_html=True)
    try:
        st.plotly_chart(
            _main_chart(df, teto, ticker, T, cs=cs),
            use_container_width=True,
            config={"displayModeBar": False, "displaylogo": False},
        )
    except Exception as e:
        st.error(f"Chart error: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # 🧠 ANÁLISE ESTRUTURADA — unified narrative (trend + technicals + valuation)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="eg-nav-anchor" id="sec-inteligencia"></div>', unsafe_allow_html=True)
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
    st.markdown('<div class="eg-nav-anchor" id="sec-proventos"></div>', unsafe_allow_html=True)
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
            )
        )
    else:
        st.info(T["no_dividends"])

    st.divider()

    # ── Dividend Calendar ─────────────────────────────────────────────────────
    st.markdown(f'<div class="eg-section-header">{T["cal_title"]}</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="eg-nav-anchor" id="sec-indicadores"></div>', unsafe_allow_html=True)
    with st.expander(T["glossary_title"], expanded=True):
        _g1, _g2 = st.columns(2)
        _gitems = T["glossary_items"]
        _gmid   = len(_gitems) // 2 + len(_gitems) % 2
        with _g1:
            for _gterm, _gdesc in _gitems[:_gmid]:
                st.markdown(f"**{_gterm}** — {_gdesc}")
        with _g2:
            for _gterm, _gdesc in _gitems[_gmid:]:
                st.markdown(f"**{_gterm}** — {_gdesc}")

    # ── Footer / Disclaimer ───────────────────────────────────────────────────
    st.divider()
    st.markdown(
        f'<div class="eg-disclaimer">{T["disclaimer"]}</div>',
        unsafe_allow_html=True,
    )
    st.caption(T["data_source"].format(version=APP_VERSION))
    st.markdown(
        "<div style='text-align:center;color:#6e7681;font-size:.72rem;margin-top:8px;'>"
        "App desenvolvido pelo Consórcio YlvorxVHM."
        "</div>",
        unsafe_allow_html=True,
    )


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
    user = st.session_state.user

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
        "</h1>",
        unsafe_allow_html=True,
    )

    # ── Navigation menu (topo da página, logo após o header) ────────────────
    _nav_items = [
        ("Cotação", "sec-cotacao"),
        ("Projeção", "sec-projecao"),
        ("Dividendos", "sec-dividendos"),
        ("Métricas", "sec-metricas"),
        ("Saúde", "sec-saude"),
        ("Técnico", "sec-tecnico"),
        ("Inteligência", "sec-inteligencia"),
        ("Proventos", "sec-proventos"),
        ("Indicadores", "sec-indicadores"),
    ]
    _nav_btns = "".join(
        f'<button class="eg-nav-btn" onclick="document.getElementById(\'{aid}\').scrollIntoView({{behavior:\'smooth\',block:\'start\'}})">{label}</button>'
        for label, aid in _nav_items
    )
    st.markdown(
        f"""<div class="eg-nav-menu">
        {_nav_btns}
        <button class="eg-nav-btn eg-nav-topo" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">Topo ↑</button>
        </div>""",
        unsafe_allow_html=True,
    )

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
