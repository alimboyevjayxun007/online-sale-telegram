"""Tiny dictionary-based i18n (uz/ru/en). Bot texts are added in app/bot/texts.py."""

from typing import Any

LANGS = ("uz", "ru", "en")
STRINGS: dict[str, dict[str, str]] = {}


def register(strings: dict[str, dict[str, str]]) -> None:
    for key, variants in strings.items():
        STRINGS[key] = variants


def t(lang: str | None, key: str, **kw: Any) -> str:
    variants = STRINGS.get(key)
    if variants is None:
        return key
    text = variants.get(lang or "uz") or variants.get("uz") or key
    return text.format(**kw) if kw else text


register(
    {
        "pay_confirmed": {
            "uz": "✅ To'lov qabul qilindi, faollashtirilmoqda...",
            "ru": "✅ Оплата получена, активируем...",
            "en": "✅ Payment received, activating...",
        },
        "order_completed": {
            "uz": "🎉 <b>Tayyor!</b> {what}\n\n🧾 Buyurtma: <code>{oid}</code>\n💵 To'landi: {paid}",
            "ru": "🎉 <b>Готово!</b> {what}\n\n🧾 Заказ: <code>{oid}</code>\n💵 Оплачено: {paid}",
            "en": "🎉 <b>Done!</b> {what}\n\n🧾 Order: <code>{oid}</code>\n💵 Paid: {paid}",
        },
        "order_failed": {
            "uz": "❌ <b>Buyurtma bajarilmadi</b> (<code>{oid}</code>)\n↩️ {refund}",
            "ru": "❌ <b>Заказ не выполнен</b> (<code>{oid}</code>)\n↩️ {refund}",
            "en": "❌ <b>Order failed</b> (<code>{oid}</code>)\n↩️ {refund}",
        },
        "refund_balance": {
            "uz": "{amount} balansingizga qaytarildi.",
            "ru": "{amount} возвращено на ваш баланс.",
            "en": "{amount} was returned to your balance.",
        },
        "refund_stars": {
            "uz": "{amount} ⭐ qaytarildi.",
            "ru": "{amount} ⭐ возвращено.",
            "en": "{amount} ⭐ refunded.",
        },
        "order_review": {
            "uz": "🔍 Buyurtmangiz (<code>{oid}</code>) tekshirilmoqda, 30 daqiqa ichida javob beramiz.",
            "ru": "🔍 Ваш заказ (<code>{oid}</code>) проверяется, ответим в течение 30 минут.",
            "en": "🔍 Your order (<code>{oid}</code>) is being reviewed; we'll reply within 30 minutes.",
        },
        "balance_topped": {
            "uz": "💼 Balansingiz <b>{amount}</b> ga to'ldirildi.",
            "ru": "💼 Баланс пополнен на <b>{amount}</b>.",
            "en": "💼 Your balance was topped up by <b>{amount}</b>.",
        },
        "balance_credit_note": {
            "uz": "💼 {amount} balansingizga yozildi: {reason}",
            "ru": "💼 {amount} зачислено на баланс: {reason}",
            "en": "💼 {amount} was credited to your balance: {reason}",
        },
        "reason_late": {
            "uz": "to'lov kech keldi (muddat tugagan edi)",
            "ru": "платёж пришёл поздно (срок истёк)",
            "en": "the payment arrived late (invoice expired)",
        },
        "reason_under": {
            "uz": "to'lov summasi yetarli emas edi, yana {need} kerak",
            "ru": "сумма платежа была недостаточной, нужно ещё {need}",
            "en": "the payment was too small, {need} more is needed",
        },
        "reason_over": {
            "uz": "ortiqcha to'lov",
            "ru": "переплата",
            "en": "overpayment",
        },
        "referral_bonus": {
            "uz": "🎁 Do'stingiz xarid qildi — sizga <b>+{amount}</b> bonus!",
            "ru": "🎁 Ваш друг сделал покупку — вам <b>+{amount}</b> бонус!",
            "en": "🎁 Your friend made a purchase — you got a <b>+{amount}</b> bonus!",
        },
        "gift_received": {
            "uz": "🎁 {who} sizga Telegram Premium ({months} oy) sovg'a qildi!",
            "ru": "🎁 {who} подарил(а) вам Telegram Premium ({months} мес.)!",
            "en": "🎁 {who} gifted you Telegram Premium ({months} mo.)!",
        },
        "what_premium": {
            "uz": "{who} ga Telegram Premium {months} oyga faollashtirildi.",
            "ru": "Telegram Premium на {months} мес. активирован для {who}.",
            "en": "Telegram Premium for {months} months was activated for {who}.",
        },
        "what_stars": {
            "uz": "{who} ga {amount} ⭐ yuborildi.",
            "ru": "{amount} ⭐ отправлено {who}.",
            "en": "{amount} ⭐ were sent to {who}.",
        },
        "who_self": {"uz": "o'zingiz", "ru": "вам", "en": "you"},
        "admin_message": {"uz": "{text}", "ru": "{text}", "en": "{text}"},
    }
)
