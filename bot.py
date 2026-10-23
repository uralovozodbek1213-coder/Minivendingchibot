import os, time, json, threading, html, sqlite3
from flask import Flask
import telebot
from telebot import types as T

bot = telebot.TeleBot(os.environ.get("TOKEN", "8664579659:AAG5pvP_8_PO4iJr9RUZpBDfrYX1TLEL6ug"))
ADMIN_ID = 8481771373
LI = {"uz": 0, "ru": 1, "en": 2}
user_lang, tmp = {}, {}
DB_FILE = "vending.db"
BK = "\n\n*(Bekor qilish uchun <b>bekor</b> deb yozing)*"
CATS = {"snack": "🍫 Sneklar va shirinliklar", "energy": "⚡ Energetik ichimliklar",
        "carbonated": "🥤 Gazlangan ichimliklar", "still": "💧 Gazlanmagan ichimliklar"}
DRINKS = ("energy", "carbonated", "still")

# ---------- SQLite Baza bilan ishlash ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Mahsulotlar jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    key TEXT PRIMARY KEY,
                    name_uz TEXT, name_ru TEXT, name_en TEXT,
                    price INTEGER, count INTEGER, start_count INTEGER,
                    added_today INTEGER, category TEXT)''')
    # Foydalanuvchilar jadvali
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT, first_name TEXT, joined_at TEXT)''')
    conn.commit()

    # Boshlang'ich mahsulotlarni yuklash (baza bo'sh bo'lsa)
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
            ("mevali_suv_05", "Gazlanmagan mevali suv 0.5L", "Вода фруктовая 0.5Л", "Fruit Still Water 0.5L", 4000, 10, 10, 0, "still")
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

def register_user(u):
    db_query("INSERT OR IGNORE INTO users VALUES (?,?,?,?)",
             (u.id, u.username or "yoq", u.first_name or "", time.strftime("%Y-%m-%d %H:%M")), commit=True)

def get_products_dict():
    rows = db_query("SELECT key, name_uz, name_ru, name_en, price, count, start_count, added_today, category FROM products", fetchall=True)
    d = {}
    for r in rows:
        d[r[0]] = {"name_uz": r[1], "name_ru": r[2], "name_en": r[3], "price": r[4], "count": r[5], "start_count": r[6], "added_today": r[7], "category": r[8]}
    return d

init_db()

# ---------- Matnlar ----------
X = {
    "kb": (("☕ Mahsulotlar va Narxlar", "🌐 Tilni tanlash", "💡 Taklifim bor", "⚠️ Shikoyatim bor"),
           ("☕ Товары и Цены", "🌐 Сменить язык", "💡 Есть предложение", "⚠️ Есть жалоба"),
           ("☕ Products & Prices", "🌐 Change Language", "💡 Suggestion", "⚠️ Complaint")),
    "chosen": ("O'zbek tili tanlandi! 🇺🇿\n\nSizga xizmat ko'rsatishdan mamnunmiz! Quyidagi menyudan kerakli bo'limni tanlashingiz mumkin:",
               "Выбран русский язык! 🇷🇺\n\nРады помочь вам! Вы можете использовать меню ниже:",
               "English language selected! 🇬🇧\n\nWe are happy to serve you! Please use the menu below:"),
    "selcat": ("📂 Mahsulotlar bo'limini tanlang:", "📂 Выберите категорию товаров:", "📂 Select product category:"),
    "snack": ("🍫 Snek va shirinliklar", "🍫 Снеки и сладости", "🍫 Snacks & Sweets"),
    "drinks": ("🥤 Ichimliklar", "🥤 Напитки", "🥤 Drinks"),
    "main": ("🔙 Asosiy menyu", "🔙 Главное меню", "🔙 Main Menu"),
    "seldrink": ("🥤 Ichimliklar turini tanlang:", "🥤 Выберите тип напитка:", "🥤 Select drink type:"),
    "back": ("🔙 Ortga", "🔙 Назад", "🔙 Back"),
    "backl": ("🔙 Ortga", "🔙 Назад к списку", "🔙 Back to list"),
    "empty": ("Hozircha bu bo'limda mahsulot mavjud emas.", "В этой категории пока нет товаров.", "There are currently no products in this category."),
    "pick": ("Mahsulotni tanlang:", "Выберите товар:", "Select product:"),
    "nf": ("Mahsulot topilmadi!", "Товар не найден!", "Product not found!"),
    "det": ("📦 <b>Mahsulot:</b> {n}\n💰 <b>Narxi:</b> {p} so'm\n📊 <b>Qurilmada mavjud:</b> {c} ta",
            "📦 <b>Товар:</b> {n}\n💰 <b>Цена:</b> {p} сум\n📊 <b>В наличии:</b> {c} шт.",
            "📦 <b>Product:</b> {n}\n💰 <b>Price:</b> {p} UZS\n📊 <b>In stock:</b> {c} pcs"),
    "out": ("🚨 Mahsulot tugadi (Xabar berish)", "🚨 Сообщить: Товар закончился", "🚨 Report: Out of stock"),
    "oos": ("📸 Iltimos, mahsulot tugaganini tasdiqlash uchun apparatdagi o'sha joyning <b>rasmini yuboring</b>:",
            "📸 Пожалуйста, отправьте фотографию автомата или полки, подтверждающую, что товар закончился:",
            "📸 Please send a photo of the vending machine shelf confirming the product is out of stock:"),
    "noph": ("❌ Rasm yuborilmadi. Iltimos, apparatdagi mahsulot joyining rasmini tushirib yuboring:",
             "❌ Это не фотография. Пожалуйста, отправьте фото товара/автомата:",
             "❌ This is not a photo. Please send a photo of the vending machine:"),
    "thx": ("🌟 <b>Katta rahmat!</b>\n\nXabaringiz va rasmingiz adminga yetkazildi. Rahmat!",
            "🌟 <b>Огромное спасибо!</b>\n\nВаше сообщение отправлено администратору.",
            "🌟 <b>Thank you very much!</b>\n\nYour report has been sent to the admin."),
}
BTN = {t: j for row in X["kb"] for j, t in enumerate(row)}

# ---------- Yordamchilar ----------
def mk(*rows, w=1):
    m = T.InlineKeyboardMarkup(row_width=w)
    m.add(*[T.InlineKeyboardButton(a, callback_data=b) for a, b in rows])
    return m

def nm(it, l="uz"): return it.get(f"name_{l}", it["name_uz"])
def snd(text, kb=None): return bot.send_message(ADMIN_ID, text, parse_mode="HTML", reply_markup=kb)
def ask(text, fn, *a): bot.register_next_step_handler(snd(text), fn, *a)
def HOME(t="🏠 Admin menyusi"): return mk((t, "am"))
def kbd(l):
    k = T.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2); k.add(*X["kb"][LI[l]]); return k

def cats_kb(l):
    i = LI[l]
    return mk((X["snack"][i], "ct:snack"), (X["drinks"][i], "dk"), (X["main"][i], "bm"))

def cat_kb(prefix, snack):
    return mk(*[(snack if k == "snack" else v, f"{prefix}:{k}") for k, v in CATS.items()], ("🏠 Admin menyusi", "am"))

def main_kb(p, home): return mk(("🍫 Snek va shirinliklar", f"{p}:snack"), ("🥤 Ichimliklar", f"{p}:drinks"), (home, "am"))
def sub_kb(p, back, home): return mk(*[(CATS[x], f"{p}:{x}") for x in DRINKS], ("🔙 Ortga", back), (home, "am"))

def stop(m, txt="Bekor qilindi."):
    if m.text and m.text.lower() == "bekor": snd(txt); amain(); return True

def bad(m, txt="Bekor qilindi."):
    if stop(m, txt): return True
    if not m.text or not m.text.isdigit(): snd("❌ Faqat raqam kiriting."); amain(); return True

# ---------- Mijoz ----------
@bot.message_handler(commands=["start"])
def start(m):
    register_user(m.from_user)
    bot.send_message(m.chat.id,
        f"Assalomu alaykum, hurmatli {html.escape(m.from_user.first_name or '')}! 😊\n"
        "Bizning vending xizmatimiz botiga xush kelibsiz.\n\n"
        "Iltimos, muloqot tilini tanlang:\n"
        "Пожалуйста, выберите язык:\n"
        "Please select your language:",
        reply_markup=mk(("🇺🇿 O'zbekcha", "sl:uz"), ("🇷🇺 Русский", "sl:ru"), ("🇬🇧 English", "sl:en"), w=3))

@bot.message_handler(func=lambda m: m.text in BTN)
def buttons(m):
    register_user(m.from_user)
    j, l = BTN[m.text], user_lang.get(m.chat.id, "uz")
    if j == 0: bot.send_message(m.chat.id, X["selcat"][LI[l]], reply_markup=cats_kb(l))
    elif j == 1: start(m)
    else:
        txt = "💡 Taklifingizni matn yoki rasm ko'rinishida yuboring:" if j == 2 else "⚠️ Shikoyatingizni matn yoki rasm ko'rinishida yuboring:"
        bot.register_next_step_handler(bot.send_message(m.chat.id, txt), feedback, j == 2)

def feedback(m, is_s):
    cid, u = m.chat.id, m.from_user; l = user_lang.get(cid, "uz")
    title = "💡 <b>YANGI TAKLIF!</b>" if is_s else "⚠️ <b>YANGI SHIKOYAT!</b>"
    info = f"{title}\n\nKimdan: @{html.escape(u.username) if u.username else 'yoq'} ({html.escape(u.first_name or '')})\nID: <code>{cid}</code>"
    kb = mk(("💬 Javob berish", f"rp:{cid}"))
    if m.content_type == "text": snd(f"{info}\n\nMatn: {html.escape(m.text)}", kb)
    elif m.content_type == "photo":
        bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=f"{info}\n\nIzoh: {html.escape(m.caption or '')}", parse_mode="HTML", reply_markup=kb)
    else: return bot.send_message(cid, "❌ Iltimos, faqat matn yoki rasm yuboring.", reply_markup=kbd(l))
    bot.send_message(cid, "🌟 Katta rahmat! Murojaatingiz adminga yetkazildi. 😊", parse_mode="HTML", reply_markup=kbd(l))

def oos_photo(m, key):
    cid = m.chat.id; l = user_lang.get(cid, "uz"); i = LI[l]
    if m.content_type != "photo":
        return bot.register_next_step_handler(bot.send_message(cid, X["noph"][i]), oos_photo, key)
    u = m.from_user
    prods = get_products_dict()
    pn = html.escape(prods.get(key, {}).get("name_uz", "Noma'lum mahsulot"))
    alert = (f"🚨 <b>DIQQAT! MAHSULOT TUGAGANI HAQIDA MUROJAAT!</b>\n\n📌 <b>Mahsulot:</b> {pn}\n"
             f"👤 <b>Mijoz:</b> @{html.escape(u.username) if u.username else 'yoq'} ({html.escape(u.first_name or '')})\n"
             f"🆔 <b>Mijoz ID:</b> <code>{cid}</code>\n\n<i>Mahsulot sonini 0 ga tushirishni tasdiqlaysizmi?</i>")
    bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=alert, parse_mode="HTML",
                   reply_markup=mk(("✅ Tasdiqlash (Soni -> 0)", f"ok:{key}:{cid}"), ("❌ Rad etish", f"no:{key}:{cid}"), w=2))
    bot.send_message(cid, X["thx"][i], parse_mode="HTML", reply_markup=kbd(l))

# ---------- Admin funksiyalari ----------
def amain(c=None):
    kb = mk(("📊 Kunlik Savdo va Statistika", "dy"), ("📥 Apparatga Mahsulot Qo'shish (+)", "as"),
            ("📢 Barcha Mijozlarga Xabar Yuborish", "bc"), ("🔄 Yangi Kun Boshlash", "rd"),
            ("📝 Narx va Sonini O'zgartirish / O'chirish", "sc"), ("➕ Yangi Mahsulot Qo'shish (Baza)", "an"))
    t = "🛠 <b>ADMIN PANEL</b>\n\nKerakli bo'limni tanlang:"
    if c: bot.edit_message_text(t, c.message.chat.id, c.message.message_id, parse_mode="HTML", reply_markup=kb)
    else: snd(t, kb)

@bot.message_handler(commands=["admin", "setprice"])
def admin_cmd(m):
    if m.chat.id == ADMIN_ID: amain()

def report():
    """To'liq hisobot + Top-3 va jami mijozlar."""
    prods = get_products_dict()
    tot = qty = 0; rows = []; sales_list = []
    
    for k, it in prods.items():
        sold = max(it["start_count"] + it["added_today"] - it["count"], 0)
        if sold > 0:
            sales_list.append((it['name_uz'], sold, sold * it["price"]))
            qty += sold
            tot += sold * it["price"]
            rows.append(f"🔹 {html.escape(it['name_uz'])} — {sold} ta — {sold * it['price']:,} so'm")

    # Jami foydalanuvchilar
    u_count = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
    
    # TOP-3 mahsulotlar
    sales_list.sort(key=lambda x: x[1], reverse=True)
    top_3 = sales_list[:3]
    top_text = "\n".join([f"🏆 {idx+1}. {item[0]} — <b>{item[1]} ta</b>" for idx, item in enumerate(top_3)]) if top_3 else "Hozircha sotuv yo'q."

    body = "\n".join(rows) if rows else "Bugun hali savdo bo'lmagan."
    return (f"📊 <b>BUGUNGI SAVDO HISOBOTI:</b>\n\n{body}\n\n"
            f"🔥 <b>ENG KO'P SOTILGAN (TOP-3):</b>\n{top_text}\n\n"
            f"📦 <b>JAMI SOTILGAN TOVAR:</b> {qty} ta\n"
            f"💰 <b>JAMI TUSHUM:</b> {tot:,} so'm\n"
            f"👥 <b>JAMI BOT FOYDALANUVCHILARI:</b> {u_count} kishi")

def broadcast_send(m):
    if stop(m, "Xabar yuborish bekor qilindi."): return
    users = db_query("SELECT user_id FROM users", fetchall=True)
    count = 0
    for u in users:
        try:
            bot.copy_message(u[0], m.chat.id, m.message_id)
            count += 1
            time.sleep(0.05) # Telegram limitidan oshmaslik uchun
        except Exception:
            pass
    snd(f"✅ Xabar <b>{count} ta</b> foydalanuvchiga muvaffaqiyatli yuborildi!", HOME())

def add_stock(m, k):
    if bad(m): return
    n = int(m.text)
    db_query("UPDATE products SET count = count + ?, added_today = added_today + ? WHERE key = ?", (n, n, k), commit=True)
    row = db_query("SELECT name_uz, count FROM products WHERE key = ?", (k,), fetchone=True)
    snd(f"✅ <code>{html.escape(row[0])}</code> ga +{n} ta qo'shildi! Hozirgi qoldiq: {row[1]} ta"); amain()

def upd(m, k, f):
    if bad(m, "Amal bekor qilindi."): return
    val = int(m.text)
    db_query(f"UPDATE products SET {f} = ? WHERE key = ?", (val, k), commit=True)
    row = db_query("SELECT name_uz FROM products WHERE key = ?", (k,), fetchone=True)
    n = html.escape(row[0])
    snd(f"✅ <code>{n}</code> narxi <b>{val:,} so'm</b>ga o'zgartirildi!" if f == "price"
        else f"✅ <code>{n}</code> soni <b>{val} ta</b> deb yangilandi!", HOME())

def add_name(m):
    if stop(m): return
    if not m.text: return amain()
    tmp["name"] = m.text
    ask(f"✍️ <code>{html.escape(m.text)}</code> narxini kiriting (masalan: 9000):{BK}", add_price)

def add_price(m):
    if bad(m): return
    tmp["price"] = int(m.text); ask(f"✍️ Apparatga nechta dona qo'ydingiz?{BK}", add_done)

def add_done(m):
    if bad(m): return
    n = int(m.text); nme = tmp["name"]; key = f"item_{int(time.time())}"
    db_query("INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?)",
             (key, nme, nme, nme, tmp["price"], n, n, 0, tmp["category"]), commit=True)
    snd(f"🎉 <b>Yangi mahsulot qo'shildi!</b>\n\n📌 Nomi: {html.escape(nme)}\n📂 Bo'lim: {CATS[tmp['category']]}\n"
        f"💰 Narxi: {tmp['price']:,} so'm\n📊 Soni: {n} ta", HOME())

def reply_user(m, uid):
    try:
        bot.send_message(uid, f"💬 <b>Ma'muriyatdan javob / Response from support:</b>\n\n{html.escape(m.text)}", parse_mode="HTML")
        snd("✅ Javob foydalanuvchiga yetkazildi!")
    except Exception as e: snd(f"❌ Xatolik yuz berdi: {html.escape(str(e))}")

# ---------- Callback Handler ----------
ADM = {"ok", "no", "am", "dy", "as", "sk", "ak", "rd", "sc", "ec", "ee", "dp", "cp", "cc", "an", "ac", "rp", "bc"}

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    a, *d = c.data.split(":"); k = d[0] if d else None
    cid, mid = c.message.chat.id, c.message.message_id
    l = user_lang.get(cid, "uz"); i = LI[l]
    ans = lambda t=None: bot.answer_callback_query(c.id, t, show_alert=bool(t))
    ed = lambda t, kb=None: bot.edit_message_text(t, cid, mid, parse_mode="HTML", reply_markup=kb)
    prods = get_products_dict()

    if a in ADM and cid != ADMIN_ID: return
    if a not in ("pd", "ok", "no", "rd"): ans()

    # --- Mijoz ---
    if a == "sl":
        user_lang[cid] = k; bot.delete_message(cid, mid)
        bot.send_message(cid, X["chosen"][LI[k]], reply_markup=kbd(k))
    elif a == "mc": ed(X["selcat"][i], cats_kb(l))
    elif a == "bm": bot.delete_message(cid, mid)
    elif a == "dk": ed(X["seldrink"][i], mk(*[(X[x][i], f"ct:{x}") for x in DRINKS], (X["back"][i], "mc")))
    elif a == "ct":
        rows = [(f"🔹 {nm(it, l)}", f"pd:{x}") for x, it in prods.items() if it["category"] == k]
        n = len(rows); rows.append((X["back"][i], "dk" if k in DRINKS else "mc"))
        ed(X["pick" if n else "empty"][i], mk(*rows))
    elif a == "pd":
        it = prods.get(k)
        if not it: ans(X["nf"][i]); ed(X["selcat"][i], cats_kb(l))
        else:
            ans()
            ed(X["det"][i].format(n=html.escape(nm(it, l)), p=f"{it['price']:,}", c=it["count"]),
               mk((X["out"][i], f"os:{k}"), (X["backl"][i], f"ct:{it['category']}")))
    elif a == "os":
        if k in prods: bot.register_next_step_handler(bot.send_message(cid, X["oos"][i], parse_mode="HTML"), oos_photo, k)

    # --- Admin: Tasdiqlash / Broadcast / Hisobot ---
    elif a in ("ok", "no"):
        it = prods.get(k); pn = html.escape(it["name_uz"]) if it else "Mahsulot"
        if a == "ok":
            db_query("UPDATE products SET count = 0 WHERE key = ?", (k,), commit=True)
            cap, al = "\n\n<b>✅ ADMIN TAROFIDAN TASDIQLANDI!</b> Soni 0 ga tushirildi.", "✅ Mahsulot soni 0 deb saqlandi!"
        else: cap, al = "\n\n<b>❌ RAD ETILDI.</b> Mahsulot soni o'zgartirilmadi.", "❌ So'rov rad etildi."
        bot.edit_message_caption(c.message.html_caption + cap, cid, mid, parse_mode="HTML")
        ans(al)
        if a == "ok":
            try: bot.send_message(d[1], f"✅ <b>{pn}</b> bo'yicha yuborgan xabaringiz admin tomonidan tasdiqlandi. Rahmat!", parse_mode="HTML")
            except Exception: pass

    elif a == "am": amain(c)
    elif a == "dy": ed(report(), HOME("🏠 Admin Menyusi"))
    elif a == "bc": ask(f"📢 Barcha foydalanuvchilarga yuboriladigan e'lon/matn/rasmni yuboring:{BK}", broadcast_send)
    elif a == "rd":
        db_query("UPDATE products SET start_count = count, added_today = 0", commit=True)
        ans("✅ Yangi kun boshlandi! Kunlik ko'rsatkichlar nolga tushirildi."); amain(c)

    # --- Admin: Boshqaruv ---
    elif a in ("as", "sc"):
        st = a == "as"
        ed("📂 Qaysi bo'limdagi mahsulotga son qo'shmoqchisiz?" if st else "📂 Qaysi bo'limdagi mahsulotlarni tahrirlamoqchisiz?",
           main_kb("sk" if st else "ec", "🏠 Admin Menyusi" if st else "🏠 Admin menyusi"))
    elif a in ("sk", "ec"):
        st = a == "sk"; home = "🏠 Admin Menyusi" if st else "🏠 Admin menyusi"
        if k == "drinks": ed("🥤 Ichimlik turini tanlang:", sub_kb(a, "as" if st else "sc", home))
        else:
            rows = [(f"➕ {it['name_uz']} (Hozir: {it['count']} ta)" if st else f"⚙️ {it['name_uz']} ({it['price']} so'm | {it['count']} ta)",
                     f"{'ak' if st else 'ee'}:{x}") for x, it in prods.items() if it["category"] == k]
            kb = mk(*rows, ("🔙 Ortga", f"{a}:drinks" if k in DRINKS else ("as" if st else "sc")), (home, "am"))
            if not rows: ed("Ushbu bo'limda mahsulot topilmadi." if st else "Ushbu bo'limda hozircha mahsulot yo'q.", kb)
            else: ed(f"📌 <b>{CATS[k]}</b> mahsulotlari:\n" + ("Soni oshiriladigan mahsulotni tanlang:" if st else "Tahrirlash yoki o'chirish uchun birini tanlang:"), kb)
    elif a == "ak":
        if k in prods: ask(f"✍️ <code>{html.escape(prods[k]['name_uz'])}</code> ga nechta dona qo'shdingiz? (masalan: 10):", add_stock, k)
    elif a == "ee":
        it = prods.get(k)
        if not it: amain(c)
        else:
            ed(f"📌 <b>{html.escape(it['name_uz'])}</b> bo'yicha amalni tanlang:",
               mk(("💰 Narxni o'zgartirish", f"cp:{k}"), ("📊 Soni (Qoldiq)ni o'zgartirish", f"cc:{k}"),
                  ("🗑 Mahsulotni BUTUNLAY O'CHIRISH", f"dp:{k}"), ("🔙 Ortga (Ro'yxatga)", f"ec:{it['category']}"),
                  ("🏠 Admin menyusi", "am")))
    elif a == "dp":
        if k in prods:
            it = prods[k]
            db_query("DELETE FROM products WHERE key = ?", (k,), commit=True)
            ed(f"🗑 <b>{html.escape(it['name_uz'])}</b> butunlay o'chirib tashlandi!",
               mk(("🔙 Ro'yxatga qaytish", f"ec:{it['category']}"), ("🏠 Admin menyusi", "am")))
        else: amain(c)
    elif a in ("cp", "cc"):
        if k not in prods: amain(c)
        else:
            what = "<b>narxni</b>" if a == "cp" else "<b>soni (dona)</b>ni"
            ask(f"✍️ <code>{html.escape(prods[k]['name_uz'])}</code> uchun yangi {what} kiriting:{BK}", upd, k, "price" if a == "cp" else "count")
    elif a == "an": ed("➕ Yangi mahsulot qaysi toifaga kiradi?", cat_kb("ac", "🍫 Sneklar"))
    elif a == "ac":
        tmp.clear(); tmp["category"] = k
        ask(f"✍️ <b>{CATS[k]}</b> uchun mahsulot nomini kiriting:{BK}", add_name)
    elif a == "rp": ask(f"✍️ Javobingizni yozing (ID: <code>{k}</code>):", reply_user, k)

# ---------- Flask va Botni Ishga tushirish ----------
app = Flask(__name__)

@app.route("/")
def home(): return "Bot is running 24/7 with SQLite!"

def run_bot():
    try: bot.set_my_commands([T.BotCommand("start", "Botni qayta ishga tushirish / Restart bot 🔄")])
    except Exception as e: print(f"Buyruqlarni o'rnatishda xatolik: {e}")
    bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
