"""
send_daily_briefing.py — Equity Guard
Job que envia briefing por e-mail apenas aos assinantes cadastrados para
a hora BRT atual (ou hora forcada via env TEST_HOUR).

Executado via GitHub Actions cron (ver .github/workflows/daily-briefing.yml).
O workflow tem 6 entradas de cron — cada uma dispara este script e ele filtra
assinantes pelo campo send_hour da tabela subscriber_hours.

Variaveis de ambiente:
  SUPABASE_URL, SUPABASE_SERVICE_KEY
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
  TEST_HOUR (opcional, 0-23): forca o filtro de hora para teste manual
"""

import os
import sys
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    if not v:
        raise RuntimeError(f"Variavel obrigatoria ausente: {name}")
    return v


def _now_brt() -> datetime:
    """Hora atual em America/Sao_Paulo, funciona com ou sem pytz."""
    try:
        import pytz
        return datetime.now(pytz.timezone("America/Sao_Paulo"))
    except Exception:
        # Fallback: UTC - 3h (BRT sem horario de verao atual no Brasil)
        return datetime.utcnow() - timedelta(hours=3)


def _current_hour_brt() -> int:
    test_hour = os.environ.get("TEST_HOUR")
    if test_hour is not None and test_hour.strip():
        try:
            return int(test_hour) % 24
        except ValueError:
            pass
    return _now_brt().hour


def _ref_trading_date(hour_brt: int) -> datetime:
    """
    Data de referencia do fechamento exibido no e-mail.
      * Envios >= 18h BRT: mercado fechou hoje -> usa data de hoje
      * Envios < 18h BRT: mercado ainda nao abriu -> usa ultimo dia util anterior
    """
    try:
        from market_status import ultimo_dia_util, dia_util_anterior
    except Exception:
        ultimo_dia_util = lambda d: d
        dia_util_anterior = lambda d: d - timedelta(days=1)
    today = _now_brt().date()
    if hour_brt >= 18:
        ref = ultimo_dia_util(today)
    else:
        ref = dia_util_anterior(today)
    return datetime.combine(ref, datetime.min.time())


def _build_html(ref_date: datetime, hour_brt: int, data: dict, unsub_url: str) -> str:
    def fmt_pct(v):
        if v is None:
            return "—"
        color = "#16a34a" if v > 0 else ("#dc2626" if v < 0 else "#6b7280")
        return f'<span style="color:{color};font-weight:700;">{v:+.2f}%</span>'

    def fmt_val(v, prefix="", digits=2):
        if v is None:
            return "—"
        return f"{prefix}{v:,.{digits}f}"

    juros = data.get("juros", {})
    commodities = data.get("commodities", {})
    fx = data.get("fx", {})
    bolsas = data.get("bolsas", {})

    def row(label, value, change=""):
        return (
            f'<tr>'
            f'<td style="padding:6px 10px;color:#334155;">{label}</td>'
            f'<td style="padding:6px 10px;text-align:right;color:#0f172a;font-weight:600;">{value}</td>'
            f'<td style="padding:6px 10px;text-align:right;">{change}</td>'
            f'</tr>'
        )

    juros_rows = [
        row("Fed Funds (EUA)", fmt_val(juros.get("fed")) + "%"),
        row("Selic (BR)", fmt_val(juros.get("selic")) + "%"),
    ]
    comm_rows = [
        row("Brent (US$/barril)", fmt_val(commodities.get("brent_val")), fmt_pct(commodities.get("brent_chg"))),
        row("WTI (US$/barril)", fmt_val(commodities.get("wti_val")), fmt_pct(commodities.get("wti_chg"))),
    ]
    fx_rows = [
        row("USD/BRL (comercial)", fmt_val(fx.get("usd_brl"), "R$ ", 4), fmt_pct(fx.get("change"))),
    ]
    bolsa_rows = [
        row(b["name"],
            fmt_val(b.get("last"), digits=0 if b.get("locale") == "br" else 2),
            fmt_pct(b.get("change")))
        for b in bolsas.get("items", [])
    ]

    def table(rows, title, emoji):
        return (
            f'<h3 style="color:#0f172a;font-size:14px;margin:18px 0 8px;'
            f'border-bottom:1px solid #e2e8f0;padding-bottom:4px;">{emoji} {title}</h3>'
            f'<table style="width:100%;border-collapse:collapse;font-size:13px;">'
            f'{"".join(rows)}</table>'
        )

    ref_str = ref_date.strftime("%d/%m/%Y")
    header_label = (
        f"Fechamento de <b>{ref_str}</b> · enviado às {hour_brt:02d}h BRT"
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#0f172a;">
  <div style="max-width:560px;margin:0 auto;padding:24px 20px;background:#ffffff;">
    <div style="padding:12px 0 20px;border-bottom:2px solid #d4af37;">
      <span style="font-size:22px;font-weight:900;letter-spacing:-.5px;color:#d4af37;">EQUITY</span>
      <span style="font-size:22px;font-weight:900;letter-spacing:-.5px;color:#0f172a;"> GUARD</span>
      <span style="background:#d4af37;color:#0f172a;font-size:11px;font-weight:800;letter-spacing:1.5px;padding:2px 8px;border-radius:12px;margin-left:8px;">BRIEFING</span>
    </div>
    <p style="color:#64748b;font-size:13px;margin:16px 0 0;">{header_label}</p>
    {table(juros_rows, "Juros", "🏦")}
    {table(comm_rows, "Commodities", "🛢️")}
    {table(fx_rows, "Dólar Comercial", "💵")}
    {table(bolsa_rows, "Bolsas", "📈")}
    <div style="margin:28px 0 12px;padding:14px;background:#fef3c7;border-left:3px solid #d4af37;border-radius:4px;font-size:12px;color:#78350f;">
      ⚠️ <b>Conteúdo informativo</b>. Não é recomendação de compra/venda.
      Consulte um consultor credenciado na CVM antes de investir.
    </div>
    <div style="text-align:center;margin:24px 0 0;">
      <a href="https://equityguard.streamlit.app/" style="background:#d4af37;color:#0f172a;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:800;font-size:13px;">Abrir app</a>
    </div>
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:28px 0 16px;">
    <p style="color:#94a3b8;font-size:11px;text-align:center;line-height:1.6;">
      Você recebeu este e-mail porque pediu o briefing diário do Equity Guard no horário das {hour_brt:02d}h BRT.<br>
      <a href="{unsub_url}" style="color:#64748b;">Cancelar assinatura</a> &middot;
      <a href="https://equityguard.streamlit.app/?page=privacidade" style="color:#64748b;">Política de Privacidade</a>
    </p>
    <p style="color:#cbd5e1;font-size:10px;text-align:center;margin:6px 0 0;">
      Equity Guard · Consórcio YlvorixVHM
    </p>
  </div>
</body></html>
"""


def _gather_market_data() -> dict:
    from data.provider import get_global_indicators, get_fx_usdbrl
    from config import FED_FUNDS_RATE, SELIC_RATE

    inds = get_global_indicators() or []
    by_name = {i["name"]: i for i in inds}

    fx = get_fx_usdbrl() or {}
    fx_data = {
        "usd_brl": fx.get("com_ask") or fx.get("ask"),
        "change": fx.get("change"),
    }

    commodities = {
        "brent_val": (by_name.get("Brent") or {}).get("last"),
        "brent_chg": (by_name.get("Brent") or {}).get("change"),
        "wti_val": (by_name.get("WTI") or {}).get("last"),
        "wti_chg": (by_name.get("WTI") or {}).get("change"),
    }

    bolsa_names = ["IBOV", "S&P 500", "NASDAQ", "FTSE"]
    bolsa_items = []
    for n in bolsa_names:
        ind = by_name.get(n)
        if ind:
            bolsa_items.append({
                "name": n,
                "last": ind.get("last"),
                "change": ind.get("change"),
                "locale": "br" if n == "IBOV" else "us",
            })

    return {
        "juros": {"fed": FED_FUNDS_RATE, "selic": SELIC_RATE},
        "commodities": commodities,
        "fx": fx_data,
        "bolsas": {"items": bolsa_items},
    }


def _send_email(to_email: str, subject: str, html: str, smtp_cfg: dict) -> bool:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_cfg["from"]
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"], timeout=20) as s:
            s.starttls()
            s.login(smtp_cfg["user"], smtp_cfg["pass"])
            s.sendmail(smtp_cfg["from"], to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"  ERRO envio {to_email}: {e}")
        return False


def main() -> None:
    smtp_cfg = {
        "host": _env("SMTP_HOST", "smtp.gmail.com"),
        "port": int(_env("SMTP_PORT", "587")),
        "user": _env("SMTP_USER"),
        "pass": _env("SMTP_PASS"),
        "from": _env("SMTP_FROM", os.environ.get("SMTP_USER", "")),
    }

    hour_brt = _current_hour_brt()
    print(f"Hora BRT alvo: {hour_brt}h")

    from auth.subscribers import get_subscribers_for_hour, mark_sent
    subs = get_subscribers_for_hour(hour_brt)
    if not subs:
        print(f"Nenhum assinante ativo para {hour_brt}h. Saindo.")
        return

    print(f"Coletando dados de mercado para {len(subs)} assinantes...")
    data = _gather_market_data()
    ref_date = _ref_trading_date(hour_brt)

    subject = f"📊 Briefing Equity Guard — {ref_date.strftime('%d/%m/%Y')} ({hour_brt:02d}h)"

    sent = 0
    failed = 0
    for sub in subs:
        email = sub["email"]
        token = sub["token"]
        unsub_url = f"https://equityguard.streamlit.app/?unsub={token}"
        html = _build_html(ref_date, hour_brt, data, unsub_url)
        if _send_email(email, subject, html, smtp_cfg):
            mark_sent(email)
            sent += 1
        else:
            failed += 1
        time.sleep(1)

    print(f"Briefing {hour_brt}h: {sent}/{len(subs)} enviados. Falhas: {failed}.")


if __name__ == "__main__":
    main()
