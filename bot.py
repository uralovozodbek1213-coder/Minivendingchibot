import os, time, html, sqlite3, datetime, threading
from flask import Flask
import telebot
from telebot import types as T
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

TOKEN = os.environ.get("TOKEN", "")
MAIN_ADMIN_ID = 8481771373
DEFAULT_PASSWORD = "admin123"
DB_FILE = "vending.db"
LOW_STOCK = 3

bot = telebot.TeleBot(TOKEN)
LANGS = ("uz", "ru", "en")
LANG_BTNS = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
user_lang, tmp = {}, {}

# ---------- Matnlar (mijozlar uchun) ----------
TX = {
    "uz": {
        "welcome": "Assalomu alaykum, <b>{name}</b>! 😊\n\nVending xizmatimizga xush kelibsiz.\nIltimos, qulay tilni tanlang:",
        "lang_set": "🇺🇿 O'zbek tili tanlandi!\n\nSizga xizmat ko'rsatishdan mamnunmiz. Quyidagi menyudan kerakli bo'limni tanlang 👇",
        "menu": ("☕ Mahsulotlar va narxlar", "🌐 Tilni o'zgartirish", "💡 Taklif yuborish", "⚠️ Shikoyat yuborish"),
        "pick_cat": "📂 Iltimos, bo'limni tanlang:",
        "snack": "🍫 Snek va shirinliklar", "drinks": "🥤 Ichimliklar",
        "cats": {"snack": "🍫 Snek va shirinliklar", "energy": "⚡ Energetik ichimliklar",
                 "carbonated": "🥤 Gazlangan ichimliklar", "still": "💧 Gazlanmagan ichimliklar"},
        "back": "🔙 Ortga", "home": "🏠 Asosiy menyu",
        "pick_drink": "🥤 Ichimlik turini tanlang:",
        "empty": "😔 Uzr, bu bo'limda hozircha mahsulot yo'q.",
        "pick_prod": "🛒 Mahsulotni tanlang:",
        "nf": "❗ Kechirasiz, mahsulot topilmadi.",
        "det": "🏷 <b>{n}</b>\n\n💰 Narxi: <b>{p} so'm</b>\n📦 Holati: {s}\n\nMahsulot tugagan bo'lsa, pastdagi tugmani bosib bizga xabar bering.",
        "st_ok": "✅ Mavjud", "st_low": "⚠️ Kam qoldi ({c} ta)", "st_out": "❌ Tugagan",
        "out_btn": "🚨 Tugaganini bildirish",
        "ask_photo": "📸 Iltimos, mahsulot joylashgan apparat qismining rasmini yuboring. Bu bizga tezroq yordam berishga yordam beradi 🙏",
        "not_photo": "❗ Iltimos, rasm yuboring yoki menyudan boshqa bo'limni tanlang.",
        "report_ok": "🌟 <b>Rahmat!</b>\n\nXabaringiz administratorlarga yetkazildi. Tez orada ko'rib chiqamiz. 🙏",
        "fb_s": "💡 Taklifingizni matn yoki rasm ko'rinishida yuboring. Fikringiz biz uchun juda muhim!",
        "fb_c": "⚠️ Shikoyatingizni matn yoki rasm ko'rinishida yuboring. Biz uni albatta ko'rib chiqamiz.",
        "fb_bad": "❗ Iltimos, faqat matn yoki rasm yuboring.",
        "fb_ok": "🌟 Rahmat! Murojaatingiz qabul qilindi. 😊",
        "report_confirmed": "✅ Xabaringiz tasdiqlandi. Yordamingiz uchun rahmat! 🙏",
        "report_rejected": "ℹ️ Kechirasiz, bu holat tasdiqlanmadi. Noqulaylik uchun uzr so'raymiz.",
    },
    "ru": {
        "welcome": "Здравствуйте, <b>{name}</b>! 😊\n\nДобро пожаловать в наш сервис вендинговых автоматов.\nПожалуйста, выберите удобный язык:",
        "lang_set": "🇷🇺 Выбран русский язык!\n\nРады помочь вам. Выберите нужный раздел в меню ниже 👇",
        "menu": ("☕ Товары и цены", "🌐 Сменить язык", "💡 Отправить предложение", "⚠️ Отправить жалобу"),
        "pick_cat": "📂 Пожалуйста, выберите раздел:",
        "snack": "🍫 Снеки и сладости", "drinks": "🥤 Напитки",
        "cats": {"snack": "🍫 Снеки и сладости", "energy": "⚡ Энергетические напитки",
                 "carbonated": "🥤 Газированные напитки", "still": "💧 Негазированные напитки"},
        "back": "🔙 Назад", "home": "🏠 Главное меню",
        "pick_drink": "🥤 Выберите тип напитка:",
        "empty": "😔 Извините, в этом разделе пока нет товаров.",
        "pick_prod": "🛒 Выберите товар:",
        "nf": "❗ Извините, товар не найден.",
        "det": "🏷 <b>{n}</b>\n\n💰 Цена: <b>{p} сум</b>\n📦 Наличие: {s}\n\nЕсли товар закончился, нажмите кнопку ниже и сообщите нам.",
        "st_ok": "✅ В наличии", "st_low": "⚠️ Осталось мало ({c} шт.)", "st_out": "❌ Закончился",
        "out_btn": "🚨 Сообщить о закончившемся товаре",
        "ask_photo": "📸 Пожалуйста, отправьте фото части автомата, где находится товар. Это поможет нам быстрее его восстановить 🙏",
        "not_photo": "❗ Пожалуйста, отправьте фото или выберите другой раздел в меню.",
        "report_ok": "🌟 <b>Спасибо!</b>\n\nВаше сообщение передано администраторам. Мы скоро его рассмотрим. 🙏",
        "fb_s": "💡 Напишите ваше предложение текстом или отправьте фото. Ваше мнение очень важно для нас!",
        "fb_c": "⚠️ Напишите вашу жалобу текстом или отправьте фото. Мы обязательно её рассмотрим.",
        "fb_bad": "❗ Пожалуйста, отправьте только текст или фото.",
        "fb_ok": "🌟 Спасибо! Ваше обращение принято. 😊",
        "report_confirmed": "✅ Ваше сообщение подтверждено. Спасибо за помощь! 🙏",
        "report_rejected": "ℹ️ К сожалению, эта информация не подтвердилась. Приносим извинения за неудобства.",
    },
    "en": {
        "welcome": "Hello, <b>{name}</b>! 😊\n\nWelcome to our vending service.\nPlease select your preferred language:",
        "lang_set": "🇬🇧 English language selected!\n\nWe are happy to serve you. Please choose a section from the menu below 👇",
        "menu": ("☕ Products & Prices", "🌐 Change Language", "💡 Send Suggestion", "⚠️ Send Complaint"),
        "pick_cat": "📂 Please choose a section:",
        "snack": "🍫 Snacks & Sweets", "drinks": "🥤 Drinks",
        "cats": {"snack": "🍫 Snacks & Sweets", "energy": "⚡ Energy Drinks",
                 "carbonated": "🥤 Carbonated Drinks", "still": "💧 Still Drinks"},
        "back": "🔙 Back", "home": "🏠 Main Menu",
        "pick_drink": "🥤 Please choose a drink type:",
        "empty": "😔 Sorry, there are no products in this section right now.",
        "pick_prod": "🛒 Please select a product:",
        "nf": "❗ Sorry, this product was not found.",
        "det": "🏷 <b>{n}</b>\n\n💰 Price: <b>{p} UZS</b>\n📦 Availability: {s}\n\nIf this product is out of stock, please tap the button below to let us know.",
        "st_ok": "✅ In stock", "st_low": "⚠️ Low stock ({c} pcs)", "st_out": "❌ Out of stock",
        "out_btn": "🚨 Report out of stock",
        "ask_photo": "📸 Please send a photo of the vending machine section where the product is. It helps us restock faster 🙏",
        "not_photo": "❗ Please send a photo, or choose another section from the menu.",
        "report_ok": "🌟 <b>Thank you!</b>\n\nYour report has been sent to our administrators. We will review it soon. 🙏",
        "fb_s": "💡 Please write your suggestion or send a photo. Your opinion matters to us!",
        "fb_c": "⚠️ Please write your complaint or send a photo. We will review it carefully.",
        "fb_bad": "❗ Please send only text or a photo.",
        "fb_ok": "🌟 Thank you! Your message has been received. 😊",
        "report_confirmed": "✅ Your report has been confirmed. Thank you for your help! 🙏",
        "report_rejected": "ℹ️ Sorry, this report could not be confirmed. We apologize for the inconvenience.",
    },
}
BTN = {label: j for lg in LANGS for j, label in enumerate(TX[lg]["menu"])}

# Admin uchun kategoriyalar (o'zbekcha)
CATS = TX["uz"]["cats"]
DRINKS = ("energy", "carbonated", "still")

# ---------- Ma'lumotlar bazasi ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    key TEXT PRIMARY KEY, name_uz TEXT, name_ru TEXT, name_en TEXT,
                    price INTEGER, count INTEGER, start_count INTEGER,
                    added_today INTEGER, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, joined_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_sales_detail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, prod_name TEXT,
                    sold_count INTEGER, revenue INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT,
                    total_items INTEGER, total_revenue INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute("INSERT OR IGNORE INTO admins VALUES (?, ?)", (MAIN_ADMIN_ID, "Bosh Admin"))
    c.execute("INSERT OR IGNORE INTO settings VALUES ('password', ?)", (DEFAULT_PASSWORD,))
    conn.commit()

    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        default_items = [
            ("snikers_mini", "Snikers mini", "Snikers mini", "Snickers mini", 7000, 10, 10, 0, "snack"),
            ("snikers_2", "Snikers 2x", "Snikers 2x", "Snickers 2x", 12000, 10, 10, 0, "snack"),
            ("moon_kok", "Moon (Ko'k)", "Moon (Синий)", "Moon (Blue)", 13000, 10, 10, 0, "snack"),
            ("moon_sariq", "Moon (Sariq)", "Moon (Желтый)", "Moon (Yellow)", 12000, 10, 10, 0, "snack"),
            ("bruni_big", "Bruni Big", "Bruni Big", "Bruni Big", 15000, 10, 10, 0, "snack"),
            ("bruni_dona", "Bruni (Dona)", "Bruni (Шт)", "Bruni (Pcs)", 3000, 10, 10, 0, "snack"),
            ("ole_big", "Ole Big", "Ole Big", "Ole Big", 13000, 10, 10, 0, "snack"),
            ("blum", "Blum", "Blum", "Blum", 3000, 10, 10, 0, "snack"),
            ("bounty", "Bounty", "Bounty", "Bounty", 5000, 10, 10, 0, "snack"),
            ("coca_cola_05", "Coca Cola 0.5L", "Coca Cola 0.5Л", "Coca Cola 0.5L", 8000, 10, 10, 0, "carbonated"),
            ("pepsi_05", "Pepsi 0.5L", "Pepsi 0.5Л", "Pepsi 0.5L", 8000, 10, 10, 0, "carbonated"),
            ("fanta_05", "Fanta 0.5L", "Fanta 0.5Л", "Fanta 0.5L", 8000, 10, 10, 0, "carbonated"),
            ("fanta_dyushes_05", "Fanta Dyushes 0.5L", "Fanta Дюшес 0.5Л", "Fanta Dyushes 0.5L", 8000, 10, 10, 0, "carbonated"),
            ("sprite_05", "Sprite 0.5L", "Sprite 0.5Л", "Sprite 0.5L", 8000, 10, 10, 0, "carbonated"),
            ("flavis_05", "Flavis 0.5L", "Flavis 0.5Л", "Flavis 0.5L", 7000, 10, 10, 0, "carbonated"),
            ("mountain_dew_05", "Mountain Dew 0.5L", "Mountain Dew 0.5Л", "Mountain Dew 0.5L", 7000, 10, 10, 0, "carbonated"),
            ("ark_tea_05", "Ark Tea 0.5L", "Ark Tea 0.5Л", "Ark Tea 0.5L", 7000, 10, 10, 0, "still"),
            ("lipton_05", "Lipton 0.5L", "Lipton 0.5Л", "Lipton 0.5L", 8000, 10, 10, 0, "still"),
            ("fuse_tea_05", "Fuse Tea 0.5L", "Fuse Tea 0.5Л", "Fuse Tea 0.5L", 8000, 10, 10, 0, "still"),
            ("ice_tea_05", "Ice Tea 0.5L", "Ice Tea 0.5Л", "Ice Tea 0.5L", 6000, 10, 10, 0, "still"),
            ("gazlanmagan_suv_05", "Gazlanmagan suv 0.5L", "Вода негазированная 0.5Л", "Still Water 0.5L", 3000, 10, 10, 0, "still"),
            ("mevali_suv_05", "Gazlanmagan mevali suv 0.5L", "Вода фруктовая 0.5Л", "Fruit Still Water 0.5L", 4000, 10, 10, 0, "still"),
        ]
        c.executemany("INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?)", default_items)
        conn.commit()
    conn.close()

def db_query(query, args=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, args)
    res = None
    if fetchone: res = c.fetchone()
    elif fetchall: res = c.fetchall()
    if commit: conn.commit()
    conn.close()
    return res

def get_admin_password():
    res = db_query("SELECT value FROM settings WHERE key='password'", fetchone=True)
    return res[0] if res else DEFAULT_PASSWORD

def get_admins_list():
    return [r[0] for r in db_query("SELECT user_id FROM admins", fetchall=True)]

def is_admin(user_id):
    return user_id in get_admins_list()

def register_user(u):
    db_query("INSERT OR IGNORE INTO users VALUES (?,?,?,?)",
             (u.id, u.username or "yoq", u.first_name or "", time.strftime("%Y-%m-%d %H:%M")), commit=True)

def get_products_dict():
    rows = db_query("SELECT key, name_uz, name_ru, name_en, price, count, start_count, added_today, category FROM products", fetchall=True)
    return {r[0]: {"name_uz": r[1], "name_ru": r[2], "name_en": r[3], "price": r[4],
                   "count": r[5], "start_count": r[6], "added_today": r[7], "category": r[8]} for r in rows}

init_db()

# ---------- Yordamchilar ----------
def tx(cid, key, **kw):
    s = TX[user_lang.get(cid, "uz")][key]
    return s.format(**kw) if kw else s

def money(n):
    return f"{n:,}".replace(",", " ")

def nm(it, lang="uz"):
    return it.get(f"name_{lang}", it["name_uz"])

def status_text(cid, it):
    c = it["count"]
    if c <= 0: return tx(cid, "st_out")
    if c <= LOW_STOCK: return tx(cid, "st_low", c=c)
    return tx(cid, "st_ok")

def status_icon(it):
    c = it["count"]
    return "❌" if c <= 0 else ("⚠️" if c <= LOW_STOCK else "✅")

def snd(cid, text, kb=None):
    return bot.send_message(cid, text, parse_mode="HTML", reply_markup=kb)

def ed(text, cid, mid, kb=None):
    return bot.edit_message_text(text, cid, mid, parse_mode="HTML", reply_markup=kb)

def snd_all_admins(text, kb=None):
    for aid in get_admins_list():
        try: snd(aid, text, kb)
        except Exception: pass

def mk(*rows, w=1):
    m = T.InlineKeyboardMarkup(row_width=w)
    m.add(*[T.InlineKeyboardButton(a, callback_data=b) for a, b in rows])
    return m

def main_reply(cid):
    lang = user_lang.get(cid, "uz")
    k = T.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    k.add(*TX[lang]["menu"])
    return k

def ask(cid, text, fn, *a):
    bot.register_next_step_handler(snd(cid, text), fn, *a)

def HOME(t="🏠 Admin menyusi"):
    return mk((t, "am"))

def stop(m, txt="Bekor qilindi."):
    if m.text and m.text.lower() == "bekor":
        snd(m.chat.id, txt); amain(cid=m.chat.id); return True
    return False

def bad(m, txt="Bekor qilindi."):
    if stop(m, txt): return True
    if not m.text or not m.text.isdigit():
        snd(m.chat.id, "❌ Faqat raqam kiriting."); amain(cid=m.chat.id); return True
    return False

# ---------- PDF ----------
def generate_pdf_report(start_date, end_date):
    pdf_filename = f"Hisobot_{start_date}_dan_{end_date}_gacha.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20,
                                 alignment=1, textColor=colors.HexColor('#1A252C'))
    elements.append(Paragraph("<b>Vending Apparat Savdo Hisoboti</b>", title_style))
    elements.append(Paragraph(f"<b>Davr:</b> {start_date} dan {end_date} gacha", styles['Normal']))
    elements.append(Spacer(1, 15))

    rows = db_query("SELECT date, prod_name, sold_count, revenue FROM daily_sales_detail WHERE date >= ? AND date <= ? ORDER BY date ASC",
                    (start_date, end_date), fetchall=True)
    if not rows:
        elements.append(Paragraph("<b>Ushbu davr bo'yicha savdo ma'lumotlari topilmadi.</b>", styles['Normal']))
    else:
        data = [["Sana", "Mahsulot Nomi", "Sotildi (ta)", "Tushum (so'm)"]]
        total_qty = total_rev = 0
        for r in rows:
            data.append([r[0], r[1], str(r[2]), f"{r[3]:,}"])
            total_qty += r[2]; total_rev += r[3]
        data.append(["JAMI", "-", str(total_qty), f"{total_rev:,}"])
        t = Table(data, colWidths=[90, 220, 90, 120])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#F2F4F4')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#27AE60')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(t)
    doc.build(elements)
    return pdf_filename

# ---------- Mijoz qismi ----------
@bot.message_handler(commands=["start"])
def start(m):
    register_user(m.from_user)
    name = html.escape(m.from_user.first_name or "do'st")
    snd(m.chat.id, f"Assalomu alaykum, <b>{name}</b>! 😊\n\nVending xizmatimizga xush kelibsiz.\n"
                   "Iltimos, qulay tilni tanlang:\n\nПожалуйста, выберите язык:\nPlease select your language:",
        mk(*[(LANG_BTNS[lg], f"sl:{lg}") for lg in LANGS], w=3))

@bot.message_handler(func=lambda m: m.text in BTN)
def menu_buttons(m):
    register_user(m.from_user)
    j = BTN[m.text]
    if j == 0:
        snd(m.chat.id, tx(m.chat.id, "pick_cat"), cats_kb(m.chat.id))
    elif j == 1:
        start(m)
    else:
        is_s = j == 2
        msg = snd(m.chat.id, tx(m.chat.id, "fb_s" if is_s else "fb_c"))
        bot.register_next_step_handler(msg, feedback, is_s)

def cats_kb(cid):
    return mk((tx(cid, "snack"), "ct:snack"), (tx(cid, "drinks"), "dk"), (tx(cid, "home"), "bm"))

def feedback(m, is_s):
    cid, u = m.chat.id, m.from_user
    title = "💡 <b>YANGI TAKLIF</b>" if is_s else "⚠️ <b>YANGI SHIKOYAT</b>"
    info = (f"{title}\n\n👤 Kimdan: @{html.escape(u.username) if u.username else 'yoq'} "
            f"({html.escape(u.first_name or '')})\n🆔 ID: <code>{cid}</code>")
    kb = mk(("💬 Javob berish", f"rp:{cid}"))
    if m.content_type == "text":
        snd_all_admins(f"{info}\n\n📝 Matn: {html.escape(m.text)}", kb)
    elif m.content_type == "photo":
        for aid in get_admins_list():
            try:
                bot.send_photo(aid, m.photo[-1].file_id, caption=f"{info}\n\nIzoh: {html.escape(m.caption or '')}",
                               parse_mode="HTML", reply_markup=kb)
            except Exception: pass
    else:
        msg = snd(cid, tx(cid, "fb_bad"))
        return bot.register_next_step_handler(msg, feedback, is_s)
    snd(cid, tx(cid, "fb_ok"), main_reply(cid))

def oos_photo(m, key):
    cid = m.chat.id
    if m.content_type != "photo":
        msg = snd(cid, tx(cid, "not_photo"))
        return bot.register_next_step_handler(msg, oos_photo, key)
    u = m.from_user
    prods = get_products_dict()
    pn = html.escape(prods.get(key, {}).get("name_uz", "Noma'lum mahsulot"))
    alert = (f"🚨 <b>MAHSULOT TUGAGANI HAQIDA XABAR</b>\n\n📌 <b>Mahsulot:</b> {pn}\n"
             f"👤 <b>Mijoz:</b> @{html.escape(u.username) if u.username else 'yoq'} ({html.escape(u.first_name or '')})\n"
             f"🆔 <b>Mijoz ID:</b> <code>{cid}</code>\n\n<i>Mahsulot sonini 0 ga tushiraymi?</i>")
    for aid in get_admins_list():
        try:
            bot.send_photo(aid, m.photo[-1].file_id, caption=alert, parse_mode="HTML",
                           reply_markup=mk(("✅ Tasdiqlash (Soni → 0)", f"ok:{key}:{cid}"),
                                           ("❌ Rad etish", f"no:{key}:{cid}"), w=2))
        except Exception: pass
    snd(cid, tx(cid, "report_ok"), main_reply(cid))

# ---------- Admin kirish ----------
@bot.message_handler(commands=["admin", "setprice"])
def admin_cmd(m):
    cid = m.chat.id
    if is_admin(cid):
        amain(cid=cid)
    else:
        msg = snd(cid, "🔒 <b>Admin panelga kirish uchun parolni kiriting:</b>\n\n<i>(Bekor qilish uchun <b>bekor</b> deb yozing)</i>")
        bot.register_next_step_handler(msg, check_admin_password)

def check_admin_password(m):
    cid = m.chat.id
    if m.text and m.text.lower() == "bekor":
        snd(cid, "Bekor qilindi."); return
    if m.text == get_admin_password():
        u = m.from_user
        info = (f"🔑 <b>YANGI ADMIN SO'ROVI</b>\n\n👤 <b>Foydalanuvchi:</b> {html.escape(u.first_name or '')} "
                f"(@{html.escape(u.username or 'yoq')})\n🆔 <b>ID:</b> <code>{cid}</code>\n\n"
                f"<i>Ushbu foydalanuvchiga admin huquqi berilsinmi?</i>")
        snd(MAIN_ADMIN_ID, info, mk(("✅ Tasdiqlash", f"adm_app:{cid}"), ("❌ Rad etish", f"adm_rej:{cid}"), w=2))
        snd(cid, "✅ <b>Parol to'g'ri!</b>\n\nSo'rovingiz Bosh adminga yuborildi. Tasdiqlangach, admin panelidan foydalanishingiz mumkin. 😊")
    else:
        snd(cid, "❌ Parol noto'g'ri. Kirish rad etildi.")

def amain(c=None, cid=None):
    chat_id = cid or c.message.chat.id
    kb = mk(("📊 Hisobotlar (Kun / Haftalik / PDF)", "rep_menu"),
            ("🏁 Kunni yopish (Qoldiq sanab kiritish)", "end_day_start"),
            ("📥 Apparatga mahsulot qo'shish (+)", "as"),
            ("📢 Barcha mijozlarga xabar yuborish", "bc"),
            ("📝 Narx va sonini o'zgartirish / o'chirish", "sc"),
            ("➕ Yangi mahsulot qo'shish (baza)", "an"),
            ("👥 Adminlar boshqaruvi va parol", "adm_mgmt"))
    t = "🛠 <b>ADMIN PANEL</b>\n\nKerakli bo'limni tanlang:"
    if c: ed(t, chat_id, c.message.message_id, kb)
    else: snd(chat_id, t, kb)

def show_admin_mgmt(c):
    cid = c.message.chat.id
    text = "👥 <b>AMALDAGI ADMINLAR RO'YXATI:</b>\n\n"
    rows = []
    for uid, name in db_query("SELECT user_id, name FROM admins", fetchall=True):
        text += f"• <code>{uid}</code> — {html.escape(name)}\n"
        if uid != MAIN_ADMIN_ID and cid == MAIN_ADMIN_ID:
            rows.append((f"❌ O'chirish: {uid}", f"del_adm:{uid}"))
    rows.append(("🔑 Parolni o'zgartirish", "change_pass"))
    rows.append(("🔙 Ortga", "am"))
    ed(text, cid, c.message.message_id, mk(*rows))

def change_password_start(c):
    msg = snd(c.message.chat.id, "🔑 <b>Yangi admin parolini kiriting:</b>\n\n<i>(Bekor qilish uchun <b>bekor</b> deb yozing)</i>")
    bot.register_next_step_handler(msg, process_new_password)

def process_new_password(m):
    cid = m.chat.id
    if stop(m, "Parol o'zgartirish bekor qilindi."): return
    new_pass = m.text.strip()
    db_query("UPDATE settings SET value=? WHERE key='password'", (new_pass,), commit=True)
    snd(cid, f"✅ Admin paroli muvaffaqiyatli o'zgartirildi!\nYangi parol: <code>{html.escape(new_pass)}</code>", HOME())

def show_report_menu(c):
    kb = mk(("📊 Bugungi real savdo hisoboti", "dy"),
            ("📅 So'nggi 7 kunlik hisobot", "rep_week"),
            ("🗓 So'nggi 30 kunlik hisobot", "rep_month"),
            ("📄 Sanalar bo'yicha PDF hisobot", "rep_pdf_start"),
            ("🔙 Ortga", "am"),
            ("🏠 Admin menyusi", "am"))
    ed("📊 <b>Qaysi davr uchun hisobotni ko'rmoqchisiz?</b>", c.message.chat.id, c.message.message_id, kb)

def get_today_report():
    tot = qty = 0; rows = []
    for it in get_products_dict().values():
        sold = max(it["start_count"] + it["added_today"] - it["count"], 0)
        if sold > 0:
            qty += sold; tot += sold * it["price"]
            rows.append(f"🔹 {html.escape(it['name_uz'])} — {sold} ta — {sold * it['price']:,} so'm")
    body = "\n".join(rows) if rows else "Bugun hali savdo hisobi yopilmagan yoki sotuv bo'lmagan."
    return (f"📊 <b>BUGUNGI REAL SAVDO HISOBOTI:</b>\n\n{body}\n\n"
            f"📦 <b>Jami sotilgan tovar:</b> {qty} ta\n💰 <b>Jami tushum:</b> {tot:,} so'm")

def get_period_report(days):
    start_date = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    rows = db_query("SELECT SUM(total_items), SUM(total_revenue) FROM sales_history WHERE date >= ?", (start_date,), fetchone=True)
    qty, tot = rows[0] or 0, rows[1] or 0
    title = "7 KUNLIK" if days == 7 else "30 KUNLIK"
    return f"📅 <b>SO'NGGI {title} SAVDO HISOBOTI:</b>\n\n📦 <b>Jami sotilgan tovar:</b> {qty} ta\n💰 <b>Jami tushum:</b> {tot:,} so'm"

def start_pdf_request(c):
    msg = snd(c.message.chat.id, "📅 <b>Boshlang'ich sanani</b> kiriting (Format: <code>YYYY-MM-DD</code>, masalan: <code>2026-10-03</code>):")
    bot.register_next_step_handler(msg, get_pdf_start_date)

def get_pdf_start_date(m):
    cid = m.chat.id
    if stop(m): return
    tmp[cid] = {"pdf_start": m.text.strip()}
    msg = snd(cid, "📅 <b>Tugash sanasini</b> kiriting (Format: <code>YYYY-MM-DD</code>, masalan: <code>2026-10-15</code>):")
    bot.register_next_step_handler(msg, get_pdf_end_date)

def get_pdf_end_date(m):
    cid = m.chat.id
    if stop(m): return
    s_date, e_date = tmp[cid]["pdf_start"], m.text.strip()
    msg_wait = snd(cid, "⏳ PDF hisobot tayyorlanmoqda, iltimos kuting...")
    try:
        pdf_path = generate_pdf_report(s_date, e_date)
        with open(pdf_path, "rb") as pdf_file:
            bot.send_document(cid, pdf_file, caption=f"📄 <b>{s_date}</b> dan <b>{e_date}</b> gacha bo'lgan savdo hisoboti.",
                              parse_mode="HTML", reply_markup=HOME())
        os.remove(pdf_path)
        bot.delete_message(cid, msg_wait.message_id)
    except Exception as ex:
        snd(cid, f"❌ PDF yaratishda xatolik yuz berdi: {html.escape(str(ex))}", HOME())

def start_end_day(c):
    cid = c.message.chat.id
    keys = list(get_products_dict().keys())
    tmp[cid] = {"keys": keys, "idx": 0, "sales_data": [], "tot_items": 0, "tot_rev": 0}
    ask_next_product_count(cid)

def ask_next_product_count(cid):
    data = tmp.get(cid)
    if not data or data["idx"] >= len(data["keys"]):
        return finish_end_day(cid)
    it = get_products_dict()[data["keys"][data["idx"]]]
    ask(cid, f"✍️ <code>{html.escape(it['name_uz'])}</code> apparatda bugun <b>nechta qoldi?</b>\n"
             f"(Boshida: {it['start_count']} ta, Qo'shildi: {it['added_today']} ta)\n\n<i>(Bekor qilish uchun <b>bekor</b> deb yozing)</i>",
        process_product_count_input, data["keys"][data["idx"]])

def process_product_count_input(m, key):
    cid = m.chat.id
    if bad(m, "Kunni yopish bekor qilindi."): return
    current_count = int(m.text)
    it = get_products_dict()[key]
    sold = max((it["start_count"] + it["added_today"]) - current_count, 0)
    rev = sold * it["price"]
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    if sold > 0:
        db_query("INSERT INTO daily_sales_detail (date, prod_name, sold_count, revenue) VALUES (?,?,?,?)",
                 (today_str, it["name_uz"], sold, rev), commit=True)
    db_query("UPDATE products SET count = ? WHERE key = ?", (current_count, key), commit=True)
    data = tmp[cid]
    data["tot_items"] += sold; data["tot_rev"] += rev; data["idx"] += 1
    ask_next_product_count(cid)

def finish_end_day(cid):
    data = tmp.pop(cid, None)
    if not data: return
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    db_query("INSERT INTO sales_history (date, total_items, total_revenue) VALUES (?,?,?)",
             (today_str, data["tot_items"], data["tot_rev"]), commit=True)
    db_query("UPDATE products SET start_count = count, added_today = 0", commit=True)
    snd(cid, f"🎉 <b>KUN MUVAFFAQIYATLI YOPILDI!</b>\n\n📊 Bugun sotildi: <b>{data['tot_items']} ta</b> tovar\n"
             f"💰 Bugungi tushum: <b>{data['tot_rev']:,} so'm</b>\n\n✅ Qoldiqlar yangilandi va ertangi kun uchun saqlandi!", HOME())

def broadcast_send(m):
    cid = m.chat.id
    if stop(m, "Xabar yuborish bekor qilindi."): return
    count = 0
    for (uid,) in db_query("SELECT user_id FROM users", fetchall=True):
        try:
            bot.copy_message(uid, cid, m.message_id)
            count += 1
            time.sleep(0.05)
        except Exception: pass
    snd(cid, f"✅ Xabar <b>{count} ta</b> foydalanuvchiga muvaffaqiyatli yuborildi!", HOME())

def add_stock(m, k):
    cid = m.chat.id
    if bad(m): return
    n = int(m.text)
    db_query("UPDATE products SET count = count + ?, added_today = added_today + ? WHERE key = ?", (n, n, k), commit=True)
    row = db_query("SELECT name_uz, count FROM products WHERE key = ?", (k,), fetchone=True)
    snd(cid, f"✅ <code>{html.escape(row[0])}</code> ga +{n} ta qo'shildi! Hozirgi qoldiq: {row[1]} ta")
    amain(cid=cid)

def upd(m, k, f):
    cid = m.chat.id
    if bad(m, "Amal bekor qilindi."): return
    val = int(m.text)
    db_query(f"UPDATE products SET {f} = ? WHERE key = ?", (val, k), commit=True)
    n = html.escape(db_query("SELECT name_uz FROM products WHERE key = ?", (k,), fetchone=True)[0])
    snd(cid, f"✅ <code>{n}</code> narxi <b>{val:,} so'm</b>ga o'zgartirildi!" if f == "price"
        else f"✅ <code>{n}</code> soni <b>{val} ta</b> deb yangilandi!", HOME())

def add_name(m):
    cid = m.chat.id
    if stop(m): return
    if not m.text: return amain(cid=cid)
    tmp.setdefault(cid, {})["name"] = m.text
    ask(cid, f"✍️ <code>{html.escape(m.text)}</code> narxini kiriting (masalan: 9000):\n\n<i>(Bekor qilish uchun <b>bekor</b> deb yozing)</i>", add_price)

def add_price(m):
    cid = m.chat.id
    if bad(m): return
    tmp[cid]["price"] = int(m.text)
    ask(cid, "✍️ Apparatga nechta dona qo'ydingiz?\n\n<i>(Bekor qilish uchun <b>bekor</b> deb yozing)</i>", add_done)

def add_done(m):
    cid = m.chat.id
    if bad(m): return
    n = int(m.text)
    nme = tmp[cid]["name"]
    key = f"item_{int(time.time())}"
    db_query("INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?)",
             (key, nme, nme, nme, tmp[cid]["price"], n, n, 0, tmp[cid]["category"]), commit=True)
    snd(cid, f"🎉 <b>Yangi mahsulot qo'shildi!</b>\n\n📌 Nomi: {html.escape(nme)}\n📂 Bo'lim: {CATS[tmp[cid]['category']]}\n"
             f"💰 Narxi: {tmp[cid]['price']:,} so'm\n📊 Soni: {n} ta", HOME())

def reply_user(m, uid):
    cid = m.chat.id
    try:
        snd(uid, f"💬 <b>Ma'muriyatdan javob / Response from support:</b>\n\n{html.escape(m.text)}")
        snd(cid, "✅ Javob foydalanuvchiga yetkazildi!")
    except Exception as e:
        snd(cid, f"❌ Xatolik yuz berdi: {html.escape(str(e))}")

# ---------- Callback ----------
ADM = {"ok", "no", "am", "dy", "as", "sk", "ak", "sc", "ec", "ee", "dp", "cp", "cc", "an", "ac", "rp", "bc",
       "rep_menu", "rep_week", "rep_month", "end_day_start", "rep_pdf_start", "adm_mgmt", "adm_app",
       "adm_rej", "del_adm", "change_pass"}

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    a, *d = c.data.split(":")
    k = d[0] if d else None
    cid, mid = c.message.chat.id, c.message.message_id
    lang = user_lang.get(cid, "uz")
    prods = get_products_dict()
    bot.answer_callback_query(c.id)

    if a in ADM and not is_admin(cid):
        return bot.answer_callback_query(c.id, "❌ Ushbu bo'lim faqat adminlar uchun!", show_alert=True)

    # ----- Mijoz -----
    if a == "sl":
        user_lang[cid] = k
        bot.delete_message(cid, mid)
        snd(cid, TX[k]["lang_set"], main_reply(cid))
    elif a == "mc":
        ed(tx(cid, "pick_cat"), cid, mid, cats_kb(cid))
    elif a == "bm":
        bot.delete_message(cid, mid)
    elif a == "dk":
        ed(tx(cid, "pick_drink"), cid, mid,
           mk(*[(TX[lang]["cats"][x], f"ct:{x}") for x in DRINKS], (tx(cid, "back"), "mc")))
    elif a == "ct":
        rows = [(f"{status_icon(it)} {nm(it, lang)} · {money(it['price'])} so'm", f"pd:{x}")
                for x, it in prods.items() if it["category"] == k]
        back = "dk" if k in DRINKS else "mc"
        if not rows:
            ed(tx(cid, "empty"), cid, mid, mk((tx(cid, "back"), back)))
        else:
            rows.append((tx(cid, "back"), back))
            ed(tx(cid, "pick_prod"), cid, mid, mk(*rows))
    elif a == "pd":
        it = prods.get(k)
        if not it:
            snd(cid, tx(cid, "nf"), cats_kb(cid))
        else:
            ed(tx(cid, "det", n=html.escape(nm(it, lang)), p=money(it["price"]), s=status_text(cid, it)),
               cid, mid, mk((tx(cid, "out_btn"), f"os:{k}"), (tx(cid, "back"), f"ct:{it['category']}")))
    elif a == "os":
        if k in prods:
            msg = snd(cid, tx(cid, "ask_photo"))
            bot.register_next_step_handler(msg, oos_photo, k)

    # ----- Admin: tasdiqlash -----
    elif a == "ok":
        cust = int(d[1])
        pn = prods.get(k, {}).get("name_uz", "Mahsulot")
        if k in prods:
            db_query("UPDATE products SET count = 0 WHERE key = ?", (k,), commit=True)
        snd(cid, f"✅ <b>{html.escape(pn)}</b> soni 0 ga tushirildi.")
        snd(cust, tx(cust, "report_confirmed"))
    elif a == "no":
        snd(cid, "❌ So'rov rad etildi.")
        snd(int(d[1]), tx(int(d[1]), "report_rejected"))
    elif a == "adm_app":
        target_id = int(k)
        row = db_query("SELECT first_name FROM users WHERE user_id=?", (target_id,), fetchone=True)
        db_query("INSERT OR REPLACE INTO admins VALUES (?,?)", (target_id, row[0] if row else "Admin"), commit=True)
        ed(f"✅ <code>{target_id}</code> ID li foydalanuvchi admin qilindi!", cid, mid)
        snd(target_id, "🎉 <b>Tabriklaymiz!</b>\n\nSiz admin etib tayinlandingiz. /admin buyrug'ini bosing.", HOME())
    elif a == "adm_rej":
        target_id = int(k)
        ed(f"❌ <code>{target_id}</code> ID li foydalanuvchi admin so'rovi rad etildi.", cid, mid)
        snd(target_id, "❌ Afsuski, admin so'rovingiz rad etildi.")
    elif a == "adm_mgmt":
        show_admin_mgmt(c)
    elif a == "change_pass":
        change_password_start(c)
    elif a == "del_adm":
        target_id = int(k)
        db_query("DELETE FROM admins WHERE user_id=?", (target_id,), commit=True)
        snd(target_id, "⚠️ Siz adminlik ro'yxatidan o'chirildingiz.")
        show_admin_mgmt(c)

    # ----- Admin: menyular -----
    elif a == "am":
        amain(c)
    elif a == "rep_menu":
        show_report_menu(c)
    elif a == "dy":
        ed(get_today_report(), cid, mid, mk(("🔙 Ortga", "rep_menu"), ("🏠 Admin menyusi", "am")))
    elif a == "rep_week":
        ed(get_period_report(7), cid, mid, mk(("🔙 Ortga", "rep_menu"), ("🏠 Admin menyusi", "am")))
    elif a == "rep_month":
        ed(get_period_report(30), cid, mid, mk(("🔙 Ortga", "rep_menu"), ("🏠 Admin menyusi", "am")))
    elif a == "rep_pdf_start":
        start_pdf_request(c)
    elif a == "end_day_start":
        start_end_day(c)
    elif a == "bc":
        ask(cid, "📢 Barcha foydalanuvchilarga yuboriladigan e'lon/matn/rasmni yuboring:\n\n<i>(Bekor qilish uchun <b>bekor</b> deb yozing)</i>", broadcast_send)
    elif a in ("as", "sc"):
        st = a == "as"
        home = "🏠 Admin menyusi"
        ed("📂 Qaysi bo'limdagi mahsulotga son qo'shmoqchisiz?" if st else "📂 Qaysi bo'limdagi mahsulotlarni tahrirlamoqchisiz?",
           cid, mid, mk((CATS["snack"], f"{'sk' if st else 'ec'}:snack"),
                        ("🥤 Ichimliklar", f"{'sk' if st else 'ec'}:drinks"),
                        ("🔙 Ortga", "am"), (home, "am")))
    elif a in ("sk", "ec"):
        st = a == "sk"
        home = "🏠 Admin menyusi"
        if k == "drinks":
            ed("🥤 Ichimlik turini tanlang:", cid, mid,
               mk(*[(CATS[x], f"{a}:{x}") for x in DRINKS], ("🔙 Ortga", "as" if st else "sc"), (home, "am")))
        else:
            rows = [(f"➕ {it['name_uz']} (Hozir: {it['count']} ta)" if st
                     else f"⚙️ {it['name_uz']} ({it['price']} so'm | {it['count']} ta)",
                     f"{'ak' if st else 'ee'}:{x}") for x, it in prods.items() if it["category"] == k]
            back = f"{a}:drinks" if k in DRINKS else ("as" if st else "sc")
            kb = mk(*rows, ("🔙 Ortga", back), (home, "am"))
            if not rows:
                ed("Ushbu bo'limda mahsulot topilmadi." if st else "Ushbu bo'limda hozircha mahsulot yo'q.", cid, mid, kb)
            else:
                ed(f"📌 <b>{CATS[k]}</b> mahsulotlari:\n" +
                   ("Soni oshiriladigan mahsulotni tanlang:" if st else "Tahrirlash yoki o'chirish uchun birini tanlang:"),
                   cid, mid, kb)
    elif a == "ak":
        if k in prods:
            ask(cid, f"✍️ <code>{html.escape(prods[k]['name_uz'])}</code> ga nechta dona qo'shdingiz? (masalan: 10):", add_stock, k)
    elif a == "ee":
        it = prods.get(k)
        if not it:
            amain(c)
        else:
            ed(f"📌 <b>{html.escape(it['name_uz'])}</b> bo'yicha amalni tanlang:", cid, mid,
               mk(("💰 Narxni o'zgartirish", f"cp:{k}"), ("📊 Soni (qoldiq)ni o'zgartirish", f"cc:{k}"),
                  ("🗑 Mahsulotni butunlay o'chirish", f"dp:{k}"), ("🔙 Ortga (ro'yxatga)", f"ec:{it['category']}"),
                  ("🏠 Admin menyusi", "am")))
    elif a == "dp":
        if k in prods:
            it = prods[k]
            db_query("DELETE FROM products WHERE key = ?", (k,), commit=True)
            ed(f"🗑 <b>{html.escape(it['name_uz'])}</b> butunlay o'chirib tashlandi!", cid, mid,
               mk(("🔙 Ro'yxatga qaytish", f"ec:{it['category']}"), ("🏠 Admin menyusi", "am")))
        else:
            amain(c)
    elif a in ("cp", "cc"):
        if k not in prods:
            amain(c)
        else:
            what = "<b>narxni</b>" if a == "cp" else "<b>soni (dona)</b>ni"
            ask(cid, f"✍️ <code>{html.escape(prods[k]['name_uz'])}</code> uchun yangi {what} kiriting:\n\n<i>(Bekor qilish uchun <b>bekor</b> deb yozing)</i>",
                upd, k, "price" if a == "cp" else "count")
    elif a == "an":
        ed("➕ Yangi mahsulot qaysi bo'limga kiradi?", cid, mid,
           mk((CATS["snack"], "ac:snack"), ("🥤 Ichimliklar", "ac:drinks"), ("🔙 Ortga", "am"), ("🏠 Admin menyusi", "am")))
    elif a == "ac":
        if k == "drinks":
            ed("🥤 Ichimlik turini tanlang:", cid, mid, mk(*[(CATS[x], f"ac:{x}") for x in DRINKS], ("🔙 Ortga", "an")))
        else:
            tmp.setdefault(cid, {})["category"] = k
            ask(cid, f"✍️ <b>{CATS[k]}</b> uchun mahsulot nomini kiriting:\n\n<i>(Bekor qilish uchun <b>bekor</b> deb yozing)</i>", add_name)
    elif a == "rp":
        ask(cid, f"✍️ Javobingizni yozing (ID: <code>{k}</code>):", reply_user, k)

# ---------- Mijoz matnli tugmalar uchun asosiy menyu tiklash ----------
@bot.message_handler(commands=["menu"])
def menu_cmd(m):
    snd(m.chat.id, tx(m.chat.id, "pick_cat"), main_reply(m.chat.id))

# ---------- Flask va ishga tushirish ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running 24/7 with Admin Approval & Management!"

def run_bot():
    try:
        bot.set_my_commands([T.BotCommand("start", "Botni qayta ishga tushirish / Restart"),
                             T.BotCommand("menu", "Asosiy menyu / Main menu")])
    except Exception as e:
        print(f"Buyruqlarni o'rnatishda xatolik: {e}")
    bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))