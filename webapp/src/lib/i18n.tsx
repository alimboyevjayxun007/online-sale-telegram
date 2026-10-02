"use client";
import { createContext, useContext } from "react";

export type Lang = "uz" | "ru" | "en";
type Dict = Record<string, string>;

const uz: Dict = {
  hello: "Salom, {name} 👋", balance: "Balans", topup: "To'ldirish", history: "Tarix", premium: "Premium", stars: "Stars",
  from: "{p} dan", up_to: "{p} gacha arzon", fast: "1–3 daqiqa", official: "Rasmiy", support247: "24/7",
  recent: "So'nggi buyurtmalar", all: "Barchasi", invite_title: "Do'stlarni taklif qiling", invite_sub: "har xariddan {p}% bonus",
  nav_home: "Asosiy", nav_wallet: "Hamyon", nav_profile: "Profil",
  tg_premium: "Telegram Premium", tg_stars: "Telegram Stars", cheaper: "Telegram'dan arzon",
  who: "Kimga?", for_me: "O'zimga", for_friend: "Do'stimga", username_ph: "@username", checking: "Tekshirilmoqda…",
  found: "{name} topildi", not_found: "Foydalanuvchi topilmadi", cannot_receive: "Premium qabul qila olmaydi", unverified: "Username tekshirilmadi — yetkazishda qayta tekshiriladi",
  duration: "Muddat", months: "{n} oy", soon: "tez kunda", best: "Eng foydali",
  amount: "Miqdor", custom_amount: "O'z miqdorim", stars_unit: "{n} ⭐", min50: "Kamida 50 ⭐",
  pay_method: "To'lov usuli", m_ton: "TON", m_stars: "Stars", m_balance: "Balans", balance_low: "Balans yetarli emas", enough: "yetarli",
  promo: "Promokodingiz bormi?", promo_apply: "Qo'llash", promo_ok: "Promokod qo'llandi", promo_bad: "Promokod yaroqsiz", total: "Jami",
  pay_ton: "💎 {a} TON to'lash", pay_stars: "⭐ {a} to'lash", pay_balance: "💼 {a} balansdan to'lash", pay_topup: "➕ To'ldirish",
  order: "Buyurtma", time_left: "{t} qoldi", expired: "Muddati o'tdi", connect_wallet: "🔗 Hamyonni ulash", confirm_wallet: "💎 Hamyonda tasdiqlash",
  manual_pay: "Qo'lda to'lash", address: "Manzil", comment: "Izoh (majburiy)", copied: "Nusxalandi",
  st_awaiting_payment: "To'lov kutilmoqda", st_paid: "To'lov qabul qilindi", st_processing: "Faollashtirilmoqda", st_completed: "Tayyor 🎉",
  st_failed: "Xato", st_needs_review: "Tekshirilmoqda", st_refunded: "Qaytarildi", st_expired: "Muddati o'tdi", st_cancelled: "Bekor qilindi",
  done_title: "Tayyor!", done_sub: "Buyurtmangiz muvaffaqiyatli bajarildi", buy_again: "Yana sotib olish", home: "Bosh sahifa", cancel_order: "Bekor qilish",
  failed_refund: "Buyurtma bajarilmadi, pul qaytarildi", review_note: "Buyurtmangiz tekshirilmoqda, 30 daqiqa ichida javob beramiz",
  orders: "Buyurtmalarim", no_orders: "Hali buyurtmalar yo'q", f_all: "Hammasi", f_active: "Jarayonda", f_completed: "Bajarilgan", f_failed: "Xato",
  repeat: "Takrorlash", help_me: "Yordam", wallet: "Hamyon", transactions: "Operatsiyalar", no_tx: "Hozircha operatsiyalar yo'q",
  topup_amount: "Summa ($)", topup_method: "To'ldirish usuli",
  profile: "Profil", language: "Til", referral: "Referal", help: "Yordam", terms: "Shartlar", admin_panel: "🛠 Admin panel",
  invited: "Taklif qilinganlar", earned: "Jami bonus", share: "📤 Ulashish", copy_link: "📋 Nusxalash", share_text: "💎 Telegram Premium va ⭐ Stars eng arzon narxda!",
  faq: "Ko'p so'raladigan savollar", contact_support: "Supportga yozish",
  faq1q: "Premium qancha vaqtda faollashadi?", faq1a: "Odatda 1–3 daqiqa.",
  faq2q: "Username'im yo'q, nima qilaman?", faq2a: "Telegram → Sozlamalar → Username orqali o'rnating.",
  faq3q: "1 oylik Premium bormi?", faq3a: "Telegram hozircha faqat 3, 6 va 12 oylik sovg'aga ruxsat beradi.",
  faq4q: "Pulim qaytadimi?", faq4a: "Buyurtma bajarilmasa, pul avtomatik qaytariladi.",
  terms_body: "Xizmat Telegram Premium va Stars sovg'a qilish orqali ishlaydi. To'lov tasdiqlangach buyurtma avtomatik bajariladi. Bajarib bo'lmasa — pul qaytariladi. Noto'g'ri username uchun mas'uliyat xaridorda.",
  retry: "Qayta urinish", error_generic: "Xatolik yuz berdi", reopen: "Ilovani Telegram'dan qayta oching", loading: "Yuklanmoqda…", back: "Orqaga", close: "Yopish",
  maintenance: "Texnik ishlar olib borilmoqda", err_INSUFFICIENT_BALANCE: "Balans yetarli emas", err_METHOD_DISABLED: "Bu usul hozir o'chirilgan",
  err_RATE_LIMITED: "Juda ko'p urinish, biroz kuting", err_PLAN_UNAVAILABLE: "Tarif mavjud emas", err_MAINTENANCE: "Texnik ishlar olib borilmoqda",
  err_INIT_DATA_EXPIRED: "Seans tugadi. Ilovani qayta oching", err_INIT_DATA_INVALID: "Ilovani Telegram ichidan oching",
  pay_cancelled: "To'lov bekor qilindi", stars_paid: "To'lov qabul qilindi", wallet_connected: "Hamyon ulandi",
};

const ru: Dict = {
  ...uz,
  hello: "Привет, {name} 👋", balance: "Баланс", topup: "Пополнить", history: "История", from: "от {p}", up_to: "дешевле до {p}", fast: "1–3 минуты", official: "Официально",
  recent: "Последние заказы", all: "Все", invite_title: "Приглашайте друзей", invite_sub: "{p}% бонус с каждой покупки",
  nav_home: "Главная", nav_wallet: "Кошелёк", nav_profile: "Профиль", cheaper: "Дешевле, чем в Telegram",
  who: "Кому?", for_me: "Себе", for_friend: "Другу", checking: "Проверяем…", found: "Найден: {name}", not_found: "Пользователь не найден", cannot_receive: "Не может получить Premium",
  unverified: "Username не проверен — проверим при выдаче",
  duration: "Срок", months: "{n} мес.", soon: "скоро", best: "Выгоднее всего", amount: "Количество", custom_amount: "Своё количество", min50: "Минимум 50 ⭐",
  pay_method: "Способ оплаты", m_balance: "Баланс", balance_low: "Недостаточно средств", enough: "достаточно", promo: "Есть промокод?", promo_apply: "Применить",
  promo_ok: "Промокод применён", promo_bad: "Промокод недействителен", total: "Итого",
  pay_ton: "💎 Оплатить {a} TON", pay_stars: "⭐ Оплатить {a}", pay_balance: "💼 Оплатить {a} с баланса", pay_topup: "➕ Пополнить",
  order: "Заказ", time_left: "Осталось {t}", expired: "Срок истёк", connect_wallet: "🔗 Подключить кошелёк", confirm_wallet: "💎 Подтвердить в кошельке",
  manual_pay: "Оплатить вручную", address: "Адрес", comment: "Комментарий (обязательно)", copied: "Скопировано",
  st_awaiting_payment: "Ожидает оплаты", st_paid: "Оплата получена", st_processing: "Активируем", st_completed: "Готово 🎉", st_failed: "Ошибка", st_needs_review: "Проверяется",
  st_refunded: "Возвращено", st_expired: "Срок истёк", st_cancelled: "Отменён", done_title: "Готово!", done_sub: "Ваш заказ успешно выполнен", buy_again: "Купить ещё", home: "На главную",
  cancel_order: "Отменить", failed_refund: "Заказ не выполнен, деньги возвращены", review_note: "Заказ проверяется, ответим в течение 30 минут",
  orders: "Мои заказы", no_orders: "Заказов пока нет", f_all: "Все", f_active: "В работе", f_completed: "Выполнены", f_failed: "Ошибки", repeat: "Повторить", help_me: "Помощь",
  wallet: "Кошелёк", transactions: "Операции", no_tx: "Операций пока нет", topup_amount: "Сумма ($)", topup_method: "Способ пополнения",
  profile: "Профиль", language: "Язык", referral: "Рефералы", help: "Помощь", terms: "Условия", invited: "Приглашено", earned: "Всего бонусов", share: "📤 Поделиться", copy_link: "📋 Копировать",
  share_text: "💎 Telegram Premium и ⭐ Stars по лучшей цене!", faq: "Частые вопросы", contact_support: "Написать в поддержку",
  faq1q: "Как быстро активируется Premium?", faq1a: "Обычно 1–3 минуты.", faq2q: "У меня нет username — что делать?", faq2a: "Установите его в Telegram → Настройки → Имя пользователя.",
  faq3q: "Есть Premium на 1 месяц?", faq3a: "Telegram пока позволяет дарить только на 3, 6 и 12 месяцев.", faq4q: "Вернут ли деньги?", faq4a: "Если заказ не выполнен, деньги возвращаются автоматически.",
  terms_body: "Сервис работает через подарок Telegram Premium и Stars. После подтверждения оплаты заказ выполняется автоматически. Если выполнить нельзя — деньги возвращаются. За неверный username отвечает покупатель.",
  retry: "Повторить", error_generic: "Произошла ошибка", reopen: "Откройте приложение заново из Telegram", loading: "Загрузка…", back: "Назад", close: "Закрыть",
  maintenance: "Ведутся технические работы", err_INSUFFICIENT_BALANCE: "Недостаточно средств", err_METHOD_DISABLED: "Этот способ сейчас отключён", err_RATE_LIMITED: "Слишком много попыток",
  err_PLAN_UNAVAILABLE: "Тариф недоступен", err_MAINTENANCE: "Ведутся технические работы", err_INIT_DATA_EXPIRED: "Сессия истекла. Откройте приложение заново", err_INIT_DATA_INVALID: "Откройте приложение из Telegram",
  pay_cancelled: "Оплата отменена", stars_paid: "Платёж принят", wallet_connected: "Кошелёк подключён",
};

const en: Dict = {
  ...uz,
  hello: "Hi, {name} 👋", balance: "Balance", topup: "Top up", history: "History", from: "from {p}", up_to: "up to {p} cheaper", fast: "1–3 minutes", official: "Official",
  recent: "Recent orders", all: "All", invite_title: "Invite friends", invite_sub: "{p}% bonus on every purchase", nav_home: "Home", nav_wallet: "Wallet", nav_profile: "Profile",
  cheaper: "Cheaper than inside Telegram", who: "Who is it for?", for_me: "For me", for_friend: "For a friend", checking: "Checking…", found: "Found: {name}", not_found: "User not found",
  cannot_receive: "Cannot receive Premium", unverified: "Username not verified — it will be checked at delivery", duration: "Duration", months: "{n} mo", soon: "coming soon", best: "Best value",
  amount: "Amount", custom_amount: "Custom amount", min50: "Minimum 50 ⭐", pay_method: "Payment method", m_balance: "Balance", balance_low: "Insufficient balance", enough: "enough",
  promo: "Have a promo code?", promo_apply: "Apply", promo_ok: "Promo code applied", promo_bad: "Invalid promo code", total: "Total",
  pay_ton: "💎 Pay {a} TON", pay_stars: "⭐ Pay {a}", pay_balance: "💼 Pay {a} from balance", pay_topup: "➕ Top up", order: "Order", time_left: "{t} left", expired: "Expired",
  connect_wallet: "🔗 Connect wallet", confirm_wallet: "💎 Confirm in wallet", manual_pay: "Pay manually", address: "Address", comment: "Comment (required)", copied: "Copied",
  st_awaiting_payment: "Awaiting payment", st_paid: "Payment received", st_processing: "Activating", st_completed: "Done 🎉", st_failed: "Failed", st_needs_review: "Under review",
  st_refunded: "Refunded", st_expired: "Expired", st_cancelled: "Cancelled", done_title: "Done!", done_sub: "Your order was completed", buy_again: "Buy again", home: "Home",
  cancel_order: "Cancel", failed_refund: "Order failed, money returned", review_note: "Your order is being reviewed; we'll reply within 30 minutes",
  orders: "My orders", no_orders: "No orders yet", f_all: "All", f_active: "Active", f_completed: "Completed", f_failed: "Failed", repeat: "Repeat", help_me: "Help",
  wallet: "Wallet", transactions: "Transactions", no_tx: "No transactions yet", topup_amount: "Amount ($)", topup_method: "Top-up method", profile: "Profile", language: "Language",
  referral: "Referral", help: "Help", terms: "Terms", invited: "Invited", earned: "Total bonus", share: "📤 Share", copy_link: "📋 Copy",
  share_text: "💎 Telegram Premium and ⭐ Stars at the lowest price!", faq: "FAQ", contact_support: "Contact support",
  faq1q: "How fast is Premium activated?", faq1a: "Usually 1–3 minutes.", faq2q: "I have no username — what now?", faq2a: "Set one in Telegram → Settings → Username.",
  faq3q: "Is there 1-month Premium?", faq3a: "Telegram currently only allows gifting 3, 6 or 12 months.", faq4q: "Will I get a refund?", faq4a: "If the order fails, the money is returned automatically.",
  terms_body: "The service works by gifting Telegram Premium and Stars. Once payment is confirmed the order is completed automatically. If it cannot be fulfilled, the money is refunded. The buyer is responsible for a wrong username.",
  retry: "Retry", error_generic: "Something went wrong", reopen: "Please reopen the app from Telegram", loading: "Loading…", back: "Back", close: "Close",
  maintenance: "Maintenance in progress", err_INSUFFICIENT_BALANCE: "Insufficient balance", err_METHOD_DISABLED: "This method is currently disabled", err_RATE_LIMITED: "Too many attempts",
  err_PLAN_UNAVAILABLE: "Plan unavailable", err_MAINTENANCE: "Maintenance in progress", err_INIT_DATA_EXPIRED: "Session expired. Reopen the app", err_INIT_DATA_INVALID: "Open the app from Telegram",
  pay_cancelled: "Payment cancelled", stars_paid: "Payment accepted", wallet_connected: "Wallet connected",
};

const DICTS: Record<Lang, Dict> = { uz, ru, en };

interface I18nCtx { lang: Lang; setLang: (l: Lang) => void; t: (key: string, vars?: Record<string, string | number>) => string }
export const I18nContext = createContext<I18nCtx>({ lang: "uz", setLang: () => {}, t: (k) => k });
export const useT = () => useContext(I18nContext);

export function makeT(lang: Lang) {
  return (key: string, vars?: Record<string, string | number>) => {
    let s = DICTS[lang][key] ?? uz[key] ?? key;
    if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, String(v));
    return s;
  };
}
