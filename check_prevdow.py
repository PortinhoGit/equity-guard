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
  (opcional) MANUAL_DATA_BASE / MANUAL_CDI_MONTH / MANUAL_BALANCED_MONTH
             — insere dados manualmente sem depender do scraper (via
               workflow_dispatch com inputs no GitHub Actions)
"""

import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _env(name: str, default: str = "") -> str:
    # .strip() evita falha de DNS quando o secret tem espaco/quebra de linha
    v = os.environ.get(name, default).strip()
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


def _manual_input() -> dict | None:
    """
    Le MANUAL_DATA_BASE / MANUAL_CDI_MONTH / MANUAL_BALANCED_MONTH do ambiente.
    Retorna dict compativel com o scraper, ou None se nao informado.
    """
    base = os.environ.get("MANUAL_DATA_BASE", "").strip()
    cdi  = os.environ.get("MANUAL_CDI_MONTH", "").strip()
    bal  = os.environ.get("MANUAL_BALANCED_MONTH", "").strip()
    if not (base and cdi and bal):
        return None
    cdi_y = os.environ.get("MANUAL_CDI_YEAR", "").strip()
    bal_y = os.environ.get("MANUAL_BALANCED_YEAR", "").strip()
    try:
        out = {
            "data_base":     base,
            "cdi_month":     float(cdi),
            "balanced_month": float(bal),
        }
        # Ano opcional: se informado, usa o numero do portal direto (sem recompor)
        if cdi_y:
            out["cdi_year"] = float(cdi_y)
        if bal_y:
            out["balanced_year"] = float(bal_y)
        return out
    except ValueError as e:
        print(f"Input manual invalido: {e}")
        return None


def main() -> None:
    today = date.today()
    force = _is_force()

    # ── Modo manual: dados informados diretamente via workflow_dispatch ────────
    manual = _manual_input()
    if manual:
        target = manual["data_base"]
        print(f"Modo manual — data_base={target}, "
              f"cdi_month={manual['cdi_month']}, "
              f"balanced_month={manual['balanced_month']}")
        force = True   # pula corte de dia 15 e idempotencia
    else:
        if today.day < 15 and not force:
            print(f"Dia {today.day} < 15. Pulando (use FORCE_RUN=1 para ignorar).")
            return
        target = _target_month(today)
        print(f"Mes-alvo: {target}")

    from supabase import create_client
    supa_url = _env("SUPABASE_URL")
    # Diagnostico: mostra so o host (sem chave) para depurar falhas de DNS
    try:
        from urllib.parse import urlparse
        print(f"Supabase host: {urlparse(supa_url).netloc!r}")
    except Exception:
        pass
    client = create_client(supa_url, _env("SUPABASE_SERVICE_KEY"))

    # Ja temos?
    existing = client.table("prevdow_history").select("data_base").eq("data_base", target).execute()
    if existing.data and not force:
        print(f"{target} ja esta no banco. Nada a fazer.")
        return

    # ── Origem dos dados: manual ou scraper ───────────────────────────────────
    if manual:
        data = manual
    else:
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

    # ── Ano acumulado: prioridade para o valor do proprio portal ──────────────
    # Regra do projeto: usar SEMPRE o numero do portal, sem substituicoes. O
    # scraper ja extrai o "Ano" (ultima coluna de seriesOriginal). So recompoe
    # a partir do historico quando o portal nao informar (fallback).
    cdi_year = data.get("cdi_year")
    balanced_year = data.get("balanced_year")

    if cdi_year is None or balanced_year is None:
        year_prefix = target.split("/")[1]
        hist = (
            client.table("prevdow_history")
            .select("data_base, cdi_month, balanced_month")
            .like("data_base", f"%/{year_prefix}")
            .execute()
        )
        if hist.data:
            cdi_prod = 1.0
            bal_prod = 1.0
            for row in hist.data:
                if row.get("cdi_month") is not None:
                    cdi_prod *= (1 + float(row["cdi_month"]) / 100)
                if row.get("balanced_month") is not None:
                    bal_prod *= (1 + float(row["balanced_month"]) / 100)
            if data.get("cdi_month") is not None:
                cdi_prod *= (1 + float(data["cdi_month"]) / 100)
            if data.get("balanced_month") is not None:
                bal_prod *= (1 + float(data["balanced_month"]) / 100)
            if cdi_year is None:
                cdi_year = round((cdi_prod - 1) * 100, 2)
            if balanced_year is None:
                balanced_year = round((bal_prod - 1) * 100, 2)

    row = {
        "data_base":      target,
        "cdi_month":      data.get("cdi_month"),
        "balanced_month": data.get("balanced_month"),
        "cdi_year":       cdi_year,
        "balanced_year":  balanced_year,
        "inserted_at":    datetime.utcnow().isoformat() + "Z",
    }
    client.table("prevdow_history").upsert(row).execute()
    print(f"  Inserido no Supabase: {row}")

    # Notifica admin
    source = "manual" if manual else "scraper"
    body = (
        f"PrevDow atualizou com dados de {target} [{source}].\n\n"
        f"Carteira DI: {data.get('cdi_month')}% no mes"
        + (f" / {cdi_year}% no ano" if cdi_year is not None else "") + "\n"
        f"Carteira Balanceada: {data.get('balanced_month')}% no mes"
        + (f" / {balanced_year}% no ano" if balanced_year is not None else "") + "\n\n"
        f"Capturado automaticamente em {datetime.utcnow().isoformat()}Z."
    )
    _send_notification(f"[Equity Guard] PrevDow {target} capturado", body)


if __name__ == "__main__":
    main()
