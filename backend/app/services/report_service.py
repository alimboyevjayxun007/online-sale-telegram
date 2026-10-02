from typing import Any


def _arrow(pct: float | None) -> str:
    if pct is None:
        return ""
    return f" {'▲' if pct >= 0 else '▼'} {abs(pct):.0f}%"


def format_stats(title: str, d: dict[str, Any], activity: dict[str, int] | None = None) -> str:
    c, ch, der, tot = d["current"], d["change_pct"], d["derived"], d["totals"]
    per = d["period"]
    lines = [
        f"📊 <b>{title}</b> ({per['start']} – {per['end']})",
        "━━━━━━━━━━━━━━━━",
        "💵 <b>MOLIYA</b>",
        f"Tushum (cash-in): {c['cash_in_usd']:.2f} ${_arrow(ch['cash_in_usd'])}",
        f"Sotuv: {c['revenue_usd']:.2f} ${_arrow(ch['revenue_usd'])}",
        f"Tannarx: {c['cost_usd']:.2f} $",
        f"Yalpi foyda: {c['gross_profit_usd']:.2f} ${_arrow(ch['gross_profit_usd'])}",
        f"Xarajatlar + referal: {(c['expenses_usd'] + c['referral_usd']):.2f} $",
        f"<b>Sof foyda: {c['net_profit_usd']:.2f} $</b>{_arrow(ch['net_profit_usd'])}",
        "━━━━━━━━━━━━━━━━",
        f"📦 <b>BUYURTMALAR</b>: {c['orders_completed']} (❌ {c['orders_failed']} · ↩️ {c['orders_refunded']})",
        f"💎 Premium: 3 oy {c['premium_3m']} · 6 oy {c['premium_6m']} · 12 oy {c['premium_12m']}",
        f"⭐ Stars: {c['stars_orders']} ta · {c['stars_sold']:,} ⭐".replace(",", " "),
        f"O'rtacha chek: {der['avg_order_usd']} $ · Marja: {der['margin_pct']}%",
    ]
    if c["revenue_by_method"]:
        lines.append("💳 " + " · ".join(f"{k} {v}$" for k, v in c["revenue_by_method"].items()))
    if c["avg_delivery_seconds"] is not None:
        lines.append(f"⏱ O'rtacha yetkazish: {int(c['avg_delivery_seconds'])} s")
    lines += [
        "━━━━━━━━━━━━━━━━",
        "👥 <b>FOYDALANUVCHILAR</b>",
        f"Jami: {tot['users']} · Yangi: {c['new_users']}{_arrow(ch['new_users'])}",
        f"Faol: {c['active_users']} · Xaridorlar: {c['paying_users']}",
    ]
    if der["conversion_pct"] is not None:
        lines.append(f"Konversiya: {der['conversion_pct']}%")
    lines.append(f"Botni bloklagan: {tot['blocked_users']}")
    if activity:
        lines.append(f"DAU {activity['dau']} · WAU {activity['wau']} · MAU {activity['mau']}")
    if tot["needs_review"]:
        lines.append(f"⚠️ Tekshirish kerak: {tot['needs_review']} ta buyurtma")
    return "\n".join(lines)
