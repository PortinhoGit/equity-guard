"""
send_daily_briefing.py — Equity Guard
Job diario que envia briefing por e-mail aos assinantes ativos.

Executado via GitHub Actions cron (ver .github/workflows/daily-briefing.yml).
Le dados de mercado via data.provider e envia via SMTP configurado em env vars.

Variaveis de ambiente esperadas (setadas como GitHub Actions secrets):
  SUPABASE_URL, SUPABASE_SERVICE_KEY
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
"""

import os
import sys
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

# Torna import relativo funcional tanto em dev quanto no runner
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    if not v:
        raise RuntimeError(f"Variavel obrigatoria ausente: {name}")
    return v


def _build_html(today_str: str, data: dict, unsub_url: str) -> str:
    """Monta HTML simples do e-mail com o briefing."""
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

    def section_row(label, value, change):
        return (
            f'<tr>'
            f'<td style="padding:6px 10px;color:#334155;">{label}</td>'
            f'<td style="padding:6px 10px;text-align:right;color:#0f172a;font-weight:600;">{value}</td>'
            f'<td style="padding:6px 10px;text-align:right;">{change}</td>'
            f'</tr>'
        )

    juros_rows = [
        section_row("Fed Funds (EUA)", fmt_val(juros.get("fed")) + "%", ""),
        section_row("Selic (BR)", fmt_val(juros.get("selic")) + "%", ""),
    ]
    comm_rows = [
        section_row("Brent (US$/barril)", fmt_val(commodities.get("brent_val")), fmt_pct(commodities.get("brent_chg"))),
        section_row("WTI (US$/barril)", fmt_val(commodities.get("wti_val")), fmt_pct(commodities.get("wti_chg"))),
    ]
    fx_rows = [
        section_row("USD/BRL (venda comercial)", fmt_val(fx.get("usd_brl"), "R$ ", 4), fmt_pct(fx.get("change"))),
    ]
    bolsa_rows = [
        section_row(b["name"], fmt_val(b.get("last"), digits=0 if b.get("locale") == "br" else 2),
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

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#0f172a;">
  <div style="max-width:560px;margin:0 auto;padding:24px 20px;background:#ffffff;">
    <div style="padding:12px 0 20px;border-bottom:2px solid #d4af37;">
      <span style="font-size:22px;font-weight:900;letter-spacing:-.5px;color:#d4af37;">EQUITY</span>
      <span style="font-size:22px;font-weight:900;letter-spacing:-.5px;color:#0f172a;"> GUARD</span>
      <span style="background:#d4af37;color:#0f172a;font-size:11px;font-weight:800;letter-spacing:1.5px;padding:2px 8px;border-radius:12px;margin-left:8px;">BRIEFING</span>
    </div>
    <p style="color:#64748b;font-size:13px;margin:16px 0 0;">
      <b>{today_str}</b> · 6h BRT · resumo do mercado
    </p>
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
      Você recebeu este e-mail porque assinou o briefing diário do Equity Guard.<br>
      <a href="{unsub_url}" style="color:#64748b;">Cancelar assinatura</a> &middot;
      <a href="https://equityguard.streamlit.app/?page=privacidade" style="color:#64748b;">Política de Privacidade</a>
    </p>
    <p style="color:#cbd5e1;font-size:10px;text-align:center;margin:6px 0 0;">
      Equity Guard · Consórcio YlvorixVHM
    </p>
  </div>
</body></html>
"""
    return html


def _gather_market_data() -> dict:
    """Coleta dados de mercado para o briefing. Usa o mesmo provider do app."""
    from data.provider import get_global_indicators, get_fx_usdbrl
    from config import FED_FUNDS_RATE, SELIC_RATE

    inds = get_global_indicators() or []
    by_name = {i["name"]: i for i in inds}

    # USD/BRL
    fx = get_fx_usdbrl() or {}
    fx_data = {
        "usd_brl": fx.get("com_ask") or fx.get("ask"),
        "change": fx.get("change"),
    }

    # Commodities
    commodities = {
        "brent_val": (by_name.get("Brent") or {}).get("last"),
        "brent_chg": (by_name.get("Brent") or {}).get("change"),
        "wti_val": (by_name.get("WTI") or {}).get("last"),
        "wti_chg": (by_name.get("WTI") or {}).get("change"),
    }

    # Bolsas (principais)
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
    # Carrega config
    smtp_cfg = {
        "host": _env("SMTP_HOST", "smtp.gmail.com"),
        "port": int(_env("SMTP_PORT", "587")),
        "user": _env("SMTP_USER"),
        "pass": _env("SMTP_PASS"),
        "from": _env("SMTP_FROM", os.environ.get("SMTP_USER", "")),
    }

    # Lista de assinantes via Supabase
    from supabase import create_client
    client = create_client(_env("SUPABASE_URL"), _env("SUPABASE_SERVICE_KEY"))
    res = client.table("subscribers").select("email, token").eq("is_active", True).execute()
    subs = res.data or []
    if not subs:
        print("Nenhum assinante ativo. Saindo.")
        return

    # Monta payload de mercado 1x (mesmo pra todos)
    print(f"Coletando dados de mercado...")
    data = _gather_market_data()

    today_str = datetime.now().strftime("%d/%m/%Y (%A)").replace(
        "Monday", "segunda").replace("Tuesday", "terça").replace(
        "Wednesday", "quarta").replace("Thursday", "quinta").replace(
        "Friday", "sexta").replace("Saturday", "sábado").replace("Sunday", "domingo")

    subject = f"📊 Briefing Equity Guard — {datetime.now().strftime('%d/%m/%Y')}"

    # Envia um a um (com pequeno delay pra nao estourar SMTP rate limit)
    sent = 0
    failed = 0
    for sub in subs:
        email = sub["email"]
        token = sub["token"]
        unsub_url = f"https://equityguard.streamlit.app/?unsub={token}"
        html = _build_html(today_str, data, unsub_url)
        if _send_email(email, subject, html, smtp_cfg):
            client.table("subscribers").update({
                "last_email_sent_at": datetime.utcnow().isoformat(),
            }).eq("email", email).execute()
            sent += 1
        else:
            failed += 1
        time.sleep(1)   # rate limit Gmail: ~20/seg max. 1s/envio é ultra seguro.

    print(f"Briefing enviado para {sent}/{len(subs)} assinantes. Falhas: {failed}.")


if __name__ == "__main__":
    main()
