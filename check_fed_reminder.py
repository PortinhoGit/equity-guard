"""
check_fed_reminder.py — Equity Guard
Roda todo dia. Se a data de ONTEM foi uma reuniao FOMC (conforme calendario
em rates.py), envia um e-mail pro admin lembrando de atualizar FED_FUNDS_RATE
no config.py com o novo valor decidido pelo Fed.

Idempotente: so dispara uma vez por reuniao (e-mail enviado no dia D+1).
"""

import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name, default)
    if not v:
        raise RuntimeError(f"Variavel obrigatoria ausente: {name}")
    return v


def _build_email_body(meeting_date: date, current_rate: float) -> tuple:
    """Retorna (subject, html)."""
    subject = f"📣 Fed decidiu a taxa — atualize FED_FUNDS_RATE (reunião {meeting_date.strftime('%d/%m/%Y')})"

    fed_statement_url = "https://www.federalreserve.gov/newsevents/pressreleases/monetary.htm"
    github_edit_url = "https://github.com/PortinhoGit/equity-guard/edit/main/config.py"
    streamlit_app_url = "https://equityguard.streamlit.app/"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#0f172a;">
<div style="max-width:560px;margin:0 auto;padding:24px 20px;background:#ffffff;">
<div style="padding:12px 0 20px;border-bottom:2px solid #d4af37;">
<span style="font-size:22px;font-weight:900;letter-spacing:-.5px;color:#d4af37;">EQUITY</span>
<span style="font-size:22px;font-weight:900;letter-spacing:-.5px;color:#0f172a;"> GUARD</span>
<span style="background:#dc2626;color:#ffffff;font-size:11px;font-weight:800;letter-spacing:1.5px;padding:2px 8px;border-radius:12px;margin-left:8px;">LEMBRETE</span>
</div>

<h2 style="color:#dc2626;font-size:18px;margin:20px 0 6px;">🏛️ FOMC decidiu a taxa ontem</h2>
<p style="color:#334155;font-size:14px;line-height:1.6;">
O Federal Reserve teve reunião em <b>{meeting_date.strftime("%d/%m/%Y")}</b>. Possivelmente a taxa mudou.
O valor atual no sistema é <b>{current_rate:.2f}%</b>.
</p>

<div style="background:#fef3c7;border-left:3px solid #d4af37;border-radius:4px;padding:14px 18px;margin:16px 0;">
<b style="color:#78350f;font-size:13px;">O que fazer:</b>
<ol style="color:#78350f;font-size:13px;line-height:1.7;margin:6px 0 0 20px;padding:0;">
<li>Ler o press release oficial do Fed</li>
<li>Identificar o novo <b>upper bound</b> do target range (ex: "3-1/4 to 3-1/2 percent" → usar 3.50)</li>
<li>Atualizar <code style="background:#fde68a;padding:1px 5px;border-radius:3px;">FED_FUNDS_RATE</code> em <code>config.py</code></li>
<li>Fazer commit — o app rebuildа sozinho</li>
</ol>
</div>

<h3 style="color:#0f172a;font-size:14px;margin:20px 0 8px;">Links úteis</h3>
<table style="width:100%;border-collapse:collapse;font-size:13px;">
<tr><td style="padding:8px 10px;">📄 Press release mais recente (Fed)</td>
<td style="padding:8px 10px;text-align:right;">
<a href="{fed_statement_url}" style="color:#d4af37;font-weight:700;">Abrir ↗</a></td></tr>
<tr><td style="padding:8px 10px;">✏️ Editar config.py direto no GitHub</td>
<td style="padding:8px 10px;text-align:right;">
<a href="{github_edit_url}" style="color:#d4af37;font-weight:700;">Editar ↗</a></td></tr>
<tr><td style="padding:8px 10px;">🌐 App em produção</td>
<td style="padding:8px 10px;text-align:right;">
<a href="{streamlit_app_url}" style="color:#d4af37;font-weight:700;">Ver ↗</a></td></tr>
</table>

<div style="margin:24px 0 8px;padding:12px;background:#f1f5f9;border-radius:6px;font-size:12px;color:#64748b;">
💡 A próxima reunião FOMC já está no calendário do <code>rates.py</code> — você não precisa atualizar a data,
só o valor da taxa.
</div>

<hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0 12px;">
<p style="color:#94a3b8;font-size:11px;text-align:center;">
Lembrete automático gerado por <a href="https://github.com/PortinhoGit/equity-guard/actions/workflows/fed-reminder.yml" style="color:#94a3b8;">fed-reminder.yml</a>
</p>
</div>
</body></html>
"""
    return subject, html


def _send_email(to_email: str, subject: str, html: str) -> bool:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.utils import formatdate

    host = _env("SMTP_HOST", "smtp.gmail.com")
    port = int(_env("SMTP_PORT", "587"))
    user = _env("SMTP_USER")
    passwd = _env("SMTP_PASS")
    sender = os.environ.get("SMTP_FROM", user)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.starttls()
            s.login(user, passwd)
            s.sendmail(sender, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Falha SMTP: {e}")
        return False


def main() -> None:
    today = date.today()
    force = os.environ.get("FORCE_RUN", "").strip() in ("1", "true", "yes")

    yesterday = today - timedelta(days=1)

    # Le calendario FOMC de rates.py
    from rates import FOMC_2026, FOMC_2027
    all_fomc = FOMC_2026 + FOMC_2027

    target = yesterday
    if force:
        # Em modo teste, considera qualquer reuniao recente do calendario
        past_meetings = [d for d in all_fomc if d <= today]
        target = max(past_meetings) if past_meetings else None

    if target not in all_fomc and not force:
        print(f"Ontem ({yesterday}) nao foi reuniao FOMC. Nada a fazer.")
        return

    # Valor atual do config (so pra citar no e-mail)
    from config import FED_FUNDS_RATE
    dest = os.environ.get("NOTIFY_EMAIL") or os.environ.get("SMTP_USER")
    if not dest:
        print("ERRO: sem e-mail de destino (NOTIFY_EMAIL ou SMTP_USER).")
        sys.exit(1)

    subject, html = _build_email_body(target, FED_FUNDS_RATE)
    ok = _send_email(dest, subject, html)
    print(f"Lembrete FOMC {target}: {'enviado' if ok else 'falhou'} para {dest}")


if __name__ == "__main__":
    main()
