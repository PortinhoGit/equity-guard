"""
check_prevdow.py — Equity Guard
Job que verifica se o portal PrevDow ja publicou os indices do mes anterior
e, se sim, salva no Supabase (tabela prevdow_history).

Regra: so faz varredura a partir do dia 15 de cada mes (portal libera dados
do mes anterior tipicamente entre dia 10-20 do mes seguinte). Em dias < 15
o script sai cedo sem fazer nada.

Idempotente: se o mes-alvo ja esta no banco, nao refaz nada.

Executado via GitHub Actions cron (ver .github/workflows/prevdow-check.yml).

Variaveis de ambiente:
  SUPABASE_URL, SUPABASE_SERVICE_KEY
  (opcional) SMTP_* — para notificar admin quando achar atualizacao
  (opcional) NOTIFY_EMAIL — destino da notificacao
  (opcional) FORCE_RUN=1 — ignora o corte de dia 15 (util pra teste manual)
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


def _target_month(today: date) -> str:
    """Retorna 'MM/YYYY' do mes anterior ao de hoje."""
    first_of_this = today.replace(day=1)
    last_of_prev = first_of_this - timedelta(days=1)
    return last_of_prev.strftime("%m/%Y")


def _is_force() -> bool:
    return os.environ.get("FORCE_RUN", "").strip() in ("1", "true", "yes")


def _send_notification(subject: str, body: str) -> None:
    """Envia e-mail de notificacao se SMTP configurado."""
    try:
        host = os.environ.get("SMTP_HOST")
        user = os.environ.get("SMTP_USER")
        passwd = os.environ.get("SMTP_PASS")
        dest = os.environ.get("NOTIFY_EMAIL") or user
        if not (host and user and passwd and dest):
            return
        port = int(os.environ.get("SMTP_PORT", "587"))
        sender = os.environ.get("SMTP_FROM", user)
        import smtplib
        from email.mime.text import MIMEText
        from email.utils import formatdate
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = dest
        msg["Date"] = formatdate(localtime=True)
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.starttls()
            s.login(user, passwd)
            s.sendmail(sender, [dest], msg.as_string())
        print(f"  Notificacao enviada para {dest}")
    except Exception as e:
        print(f"  Falha ao notificar: {e}")


def main() -> None:
    today = date.today()
    force = _is_force()

    if today.day < 15 and not force:
        print(f"Dia {today.day} < 15. Pulando (use FORCE_RUN=1 para ignorar).")
        return

    target = _target_month(today)
    print(f"Mes-alvo: {target}")

    from supabase import create_client
    client = create_client(_env("SUPABASE_URL"), _env("SUPABASE_SERVICE_KEY"))

    # Ja temos?
    existing = client.table("prevdow_history").select("data_base").eq("data_base", target).execute()
    if existing.data and not force:
        print(f"{target} ja esta no banco. Nada a fazer.")
        return

    # Scraper
    try:
        from data.prevdow_scraper import get_rentabilidade_prevdow
    except Exception as e:
        print(f"Falha ao importar scraper: {e}")
        return

    print("Rodando scraper do portal PrevDow...")
    data = get_rentabilidade_prevdow()
    if not data:
        print("Scraper retornou vazio — portal pode estar indisponivel ou sem dados ainda.")
        return

    fetched_base = data.get("data_base")
    print(f"Scraper retornou data_base={fetched_base}, "
          f"cdi_month={data.get('cdi_month')}, "
          f"balanced_month={data.get('balanced_month')}")

    if fetched_base != target:
        print(f"Portal ainda mostra {fetched_base}, mes-alvo e {target}. "
              f"Tentaremos de novo no proximo run.")
        return

    # Calcula ano acumulado a partir do historico do mesmo ano (se existir)
    year_prefix = target.split("/")[1]
    hist = (
        client.table("prevdow_history")
        .select("data_base, cdi_month, balanced_month")
        .like("data_base", f"%/{year_prefix}")
        .execute()
    )
    cdi_year = None
    balanced_year = None
    if hist.data:
        # Calcula acumulado composto: prod(1+r) - 1
        cdi_prod = 1.0
        bal_prod = 1.0
        for row in hist.data:
            if row.get("cdi_month") is not None:
                cdi_prod *= (1 + float(row["cdi_month"]) / 100)
            if row.get("balanced_month") is not None:
                bal_prod *= (1 + float(row["balanced_month"]) / 100)
        # Inclui o mes atual que estamos inserindo
        if data.get("cdi_month") is not None:
            cdi_prod *= (1 + float(data["cdi_month"]) / 100)
        if data.get("balanced_month") is not None:
            bal_prod *= (1 + float(data["balanced_month"]) / 100)
        cdi_year = round((cdi_prod - 1) * 100, 2)
        balanced_year = round((bal_prod - 1) * 100, 2)

    row = {
        "data_base": target,
        "cdi_month": data.get("cdi_month"),
        "balanced_month": data.get("balanced_month"),
        "cdi_year": cdi_year,
        "balanced_year": balanced_year,
    }
    client.table("prevdow_history").upsert(row).execute()
    print(f"  Inserido no Supabase: {row}")

    # Notifica admin
    body = (
        f"PrevDow atualizou com dados de {target}.\n\n"
        f"Carteira DI: {data.get('cdi_month')}% no mes"
        + (f" / {cdi_year}% no ano" if cdi_year is not None else "") + "\n"
        f"Carteira Balanceada: {data.get('balanced_month')}% no mes"
        + (f" / {balanced_year}% no ano" if balanced_year is not None else "") + "\n\n"
        f"Capturado automaticamente em {datetime.now().isoformat()}."
    )
    _send_notification(f"[Equity Guard] PrevDow {target} capturado", body)


if __name__ == "__main__":
    main()
