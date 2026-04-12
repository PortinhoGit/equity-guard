"""
ui/payment.py — Equity Guard
Tela de recarga de créditos via Pix / Mercado Pago.

Integração real: configure MP_ACCESS_TOKEN em .env e descomente
o bloco SDK abaixo. O fluxo é:
  1. Usuário escolhe plano
  2. App cria preferência no Mercado Pago → obtém link/QR Pix
  3. Webhook atualiza créditos após confirmação de pagamento

TODO: adicionar endpoint de webhook (ex: Flask/FastAPI) para receber
      notificações do Mercado Pago e chamar auth.manager.add_credits().
"""

import streamlit as st
import json
import os
from pathlib import Path
from typing import Dict

# ─── Mock: códigos de ativação para testes (remover em produção) ──────────────
_DEMO_CODES: Dict[str, int] = {
    "EG-DEMO-50":  50,
    "EG-DEMO-100": 100,
    "EG-DEMO-200": 200,
}

_CODES_DB = Path(__file__).parent.parent / "activation_codes.json"


def _load_codes() -> Dict[str, int]:
    if _CODES_DB.exists():
        try:
            return json.loads(_CODES_DB.read_text(encoding="utf-8"))
        except Exception:
            pass
    return dict(_DEMO_CODES)


def _mark_used(code: str) -> None:
    codes = _load_codes()
    codes.pop(code, None)
    _CODES_DB.write_text(
        json.dumps(codes, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _add_credits(email: str, amount: int) -> None:
    """Adiciona créditos ao usuário no users_db.json."""
    import json as _j
    db_path = Path(__file__).parent.parent / "users_db.json"
    if not db_path.exists():
        return
    db = _j.loads(db_path.read_text(encoding="utf-8"))
    user = db["users"].get(email)
    if user:
        current = user.get("credits", 0)
        if current != -1:   # não mexe em admin
            user["credits"] = current + amount
        db["users"][email] = user
        db_path.write_text(_j.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")


# ─── Renderização ─────────────────────────────────────────────────────────────

def render_payment_page(user: dict, T: dict) -> None:
    """
    Exibe a tela de pagamento. Chamada quando créditos chegam a zero.
    Após função retornar, app.py deve chamar st.stop().
    """
    is_anon = user.get("is_anonymous", False)
    email   = user.get("email", "")

    # ── Botão voltar ──────────────────────────────────────────────────────────
    if st.button(T["back_to_app"]):
        # Logout → usuário retorna à tela de login para criar conta
        for k in ["user", "df", "dividends", "fundamentals",
                  "last_ticker", "last_period"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown(
        f"<h2 style='color:#d4af37;margin-bottom:0;'>{T['payment_title']}</h2>"
        f"<p style='color:#8b949e;margin-top:4px;'>{T['payment_subtitle']}</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Seleção de plano ──────────────────────────────────────────────────────
    plans = [
        {
            "key":     "starter",
            "label":   T["plan_starter"],
            "price":   T["plan_prices"]["starter"],
            "credits": T["plan_credits"]["starter"],
        },
        {
            "key":     "pro",
            "label":   T["plan_pro"],
            "price":   T["plan_prices"]["pro"],
            "credits": T["plan_credits"]["pro"],
        },
        {
            "key":     "premium",
            "label":   T["plan_premium"],
            "price":   T["plan_prices"]["premium"],
            "credits": T["plan_credits"]["premium"],
        },
    ]

    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]
    selected_plan = st.session_state.get("selected_plan", "pro")

    for i, (plan, col) in enumerate(zip(plans, cols)):
        with col:
            is_sel = (plan["key"] == selected_plan)
            border = "#d4af37" if is_sel else "#30363d"
            bg     = "rgba(212,175,55,0.08)" if is_sel else "#161b22"
            st.markdown(
                f"<div style='background:{bg};border:2px solid {border};"
                f"border-radius:14px;padding:20px 16px;text-align:center;'>"
                f"<div style='font-size:0.82rem;color:#8b949e;'>{plan['label']}</div>"
                f"<div style='font-size:1.8rem;font-weight:900;color:#e6edf3;"
                f"margin:8px 0;'>{plan['price']}</div>"
                f"<div style='font-size:0.78rem;color:#d4af37;'>"
                f"{'⭐ ' if is_sel else ''}{plan['credits']} créditos</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                f"{'✅ ' if is_sel else ''}Selecionar",
                key=f"sel_{plan['key']}",
                use_container_width=True,
            ):
                st.session_state.selected_plan = plan["key"]
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Área Pix ──────────────────────────────────────────────────────────────
    sel = next(p for p in plans if p["key"] == selected_plan)
    col_qr, col_code = st.columns([1, 1])

    with col_qr:
        st.markdown(f"#### {T['pix_title']}")
        # ── Placeholder QR ────────────────────────────────────────────────────
        # TODO: substituir pelo QR real do Mercado Pago:
        #   import mercadopago
        #   sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))
        #   pref = sdk.preference().create({
        #       "items": [{"title": sel["label"], "unit_price": price_float,
        #                  "quantity": 1, "currency_id": "BRL"}],
        #       "payment_methods": {"excluded_payment_types": [{"id": "credit_card"}]},
        #   })
        #   pix_qr = pref["response"]["point_of_interaction"]["transaction_data"]["qr_code_base64"]
        #   st.image(f"data:image/png;base64,{pix_qr}")
        st.markdown(
            "<div style='"
            "width:180px;height:180px;margin:0 auto;"
            "background:#1c2128;border:2px dashed #30363d;"
            "border-radius:10px;display:flex;align-items:center;"
            "justify-content:center;text-align:center;"
            "color:#6e7681;font-size:0.78rem;padding:16px;"
            "box-sizing:border-box;'>"
            f"{T['pix_placeholder'].replace(chr(10), '<br>')}"
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption(T["mp_note"])

    with col_code:
        st.markdown(f"#### {T['activation_code']}")
        # ── Código de ativação (alternativa / testes) ─────────────────────────
        st.caption("Para testar: `EG-DEMO-50`, `EG-DEMO-100`, `EG-DEMO-200`")
        code_input = st.text_input(
            T["activation_code"],
            placeholder="EG-XXXXXX",
            label_visibility="collapsed",
            key="activation_code_input",
        )
        if st.button(T["activate_btn"], type="primary", use_container_width=True):
            code = code_input.strip().upper()
            valid_codes = _load_codes()
            if code in valid_codes:
                credits_to_add = valid_codes[code]
                if not is_anon and email:
                    _add_credits(email, credits_to_add)
                    # Atualiza session_state
                    from auth.manager import load_user
                    refreshed = load_user(email)
                    if refreshed:
                        st.session_state.user = refreshed
                _mark_used(code)
                st.success(f"✅ +{credits_to_add} créditos adicionados!")
                st.balloons()
                st.session_state.pop("selected_plan", None)
                st.rerun()
            else:
                st.error(T["invalid_code"])

    st.divider()
    # ── Disclaimer ────────────────────────────────────────────────────────────
    st.caption(T["disclaimer"])
