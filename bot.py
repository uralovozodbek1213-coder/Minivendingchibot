import os, time, json, threading, html
from flask import Flask
import telebot
from telebot import types as T

bot = telebot.TeleBot(os.environ.get("TOKEN", "8664579659:AAG5pvP_8_PO4iJr9RUZpBDfrYX1TLEL6ug"))
ADMIN_ID = 8481771373
LI = {"uz": 0, "ru": 1, "en": 2}
user_lang, tmp = {}, {}
DATA_FILE = "products.json"
BK = "\n\n*(Bekor qilish uchun <b>bekor</b> deb yozing)*"
CATS = {"snack": "🍫 Sneklar va shirinliklar", "energy": "⚡ Energetik ichimliklar",
        "carbonated": "🥤 Gazlangan ichimliklar", "still": "💧 Gazlanmagan ichimliklar"}
DRINKS = ("energy", "carbonated", "still")

# Mijozga chiqadigan matnlar: (uz, ru, en)
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
    "energy": ("⚡ Energetik ichimliklar", "⚡ Энергетические напитки", "⚡ Energy Drinks"),
    "carbonated": ("🥤 Gazlangan ichimliklar", "🥤 Газированные напитки", "🥤 Carbonated Drinks"),
    "still": ("💧 Gazlanmagan ichimliklar", "💧 Негазированные напитки", "💧 Still Drinks"),
    "back": ("🔙 Ortga", "🔙 Назад", "🔙 Back"),
    "backl": ("🔙 Ortga", "🔙 Назад к списку", "🔙 Back to list"),
    "empty": ("Hozircha bu bo'limda mahsulot mavjud emas.", "В этой категории пока нет товаров.",
              "There are currently no products in this category."),
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
BTN = {t: j for row in X["kb"] for j, t in enumerate(row)}  # 0 mahsulot, 1 til, 2 taklif, 3 shikoyat

# ---------- Ma'lumotlar ----------
def dump(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=4)

def save(): dump(PRODUCTS)

def P(uz, ru, en, price, n, cat):
    return {"name_uz": uz, "name_ru": ru, "name_en": en, "price": price, "count": n, "start_count": n, "added_today": 0, "category": cat}

def load():
    if not os.path.exists(DATA_FILE):
        d = {
            # Shirinliklar va Sneklar
            "snikers_mini": P("Snikers mini", "Snikers mini", "Snickers mini", 7000, 10, "snack"),
            "snikers_2": P("Snikers 2x", "Snikers 2x", "Snickers 2x", 12000, 10, "snack"),
            "moon_kok": P("Moon (Ko'k)", "Moon (Синий)", "Moon (Blue)", 13000, 10, "snack"),
            "moon_sariq": P("Moon (Sariq)", "Moon (Желтый)", "Moon (Yellow)", 12000, 10, "snack"),
            "bruni_big": P("Bruni Big", "Bruni Big", "Bruni Big", 15000, 10, "snack"),
            "bruni_dona": P("Bruni (Dona)", "Bruni (Шт)", "Bruni (Pcs)", 3000, 10, "snack"),
            "ole_big": P("Ole Big", "Ole Big", "Ole Big", 13000, 10, "snack"),
            "blum": P("Blum", "Blum", "Blum", 3000, 10, "snack"),
            "bounty": P("Bounty", "Bounty", "Bounty", 5000, 10, "snack"),

            # Gazlangan Ichimliklar
            "coca_cola_05": P("Coca Cola 0.5L", "Coca Cola 0.5Л", "Coca Cola 0.5L", 8000, 10, "carbonated"),
            "pepsi_05": P("Pepsi 0.5L", "Pepsi 0.5Л", "Pepsi 0.5L", 8000, 10, "carbonated"),
            "fanta_05": P("Fanta 0.5L", "Fanta 0.5Л", "Fanta 0.5L", 8000, 10, "carbonated"),
            "fanta_dyushes_05": P("Fanta Dyushes 0.5L", "Fanta Дюшес 0.5Л", "Fanta Dyushes 0.5L", 8000, 10, "carbonated"),
            "sprite_05": P("Sprite 0.5L", "Sprite 0.5Л", "Sprite 0.5L", 8000, 10, "carbonated"),
            "flavis_05": P("Flavis 0.5L", "Flavis 0.5Л", "Flavis 0.5L", 7000, 10, "carbonated"),
            "mountain_dew_05": P("Mountain Dew 0.5L", "Mountain Dew 0.5Л", "Mountain Dew 0.5L", 7000, 10, "carbonated"),

            # Gazlanmagan Ichimliklar
            "ark_tea_05": P("Ark Tea 0.5L", "Ark Tea 0.5Л", "Ark Tea 0.5L", 7000, 10, "still"),
            "lipton_05": P("Lipton 0.5L", "Lipton 0.5Л", "Lipton 0.5L", 8000, 10, "still"),
            "fuse_tea_05": P("Fuse Tea 0.5L", "Fuse Tea 0.5Л", "Fuse Tea 0.5L", 8000, 10, "still"),
            "ice_tea_05": P("Ice Tea 0.5L", "Ice Tea 0.5Л", "Ice Tea 0.5L", 6000, 10, "still"),
            "gazlanmagan_suv_05": P("Gazlanmagan suv 0.5L", "Вода негазированная 0.5Л", "Still Water 0.5L", 3000, 10, "still"),
            "mevali_suv_05": P("Gazlanmagan mevali suv 0.5L", "Вода фруктовая 0.5Л", "Fruit Still Water 0.5L", 4000, 10, "still")
        }
        dump(d); return d
    try:
        with open(DATA_FILE, encoding="utf-8") as f: d = json.load(f)
        for v in d.values():
            v.setdefault("start_count", v["count"]); v.setdefault("added_today", 0)
        return d
    except Exception: return {}

PRODUCTS = load()

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

def cat_kb(prefix, snack):  # admin: yangi mahsulot toifalari
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
    bot.send_message(m.chat.id,
        f"Assalomu alaykum, hurmatli {html.escape(m.from_user.first_name or '')}! 😊\n"
        "Bizning vending xizmatimiz botiga xush kelibsiz.\n\n"
        "Iltimos, muloqot tilini tanlang:\n"
        "Пожалуйста, выберите язык:\n"
        "Please select your language:",
        reply_markup=mk(("🇺🇿 O'zbekcha", "sl:uz"), ("🇷🇺 Русский", "sl:ru"), ("🇬🇧 English", "sl:en"), w=3))

@bot.message_handler(func=lambda m: m.text in BTN)
def buttons(m):
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
    pn = html.escape(PRODUCTS.get(key, {}).get("name_uz", "Noma'lum mahsulot"))
    alert = (f"🚨 <b>DIQQAT! MAHSULOT TUGAGANI HAQIDA MUROJAAT!</b>\n\n📌 <b>Mahsulot:</b> {pn}\n"
             f"👤 <b>Mijoz:</b> @{html.escape(u.username) if u.username else 'yoq'} ({html.escape(u.first_name or '')})\n"
             f"🆔 <b>Mijoz ID:</b> <code>{cid}</code>\n\n<i>Mahsulot sonini 0 ga tushirishni tasdiqlaysizmi?</i>")
    bot.send_photo(ADMIN_ID, m.photo[-1].file_id, caption=alert, parse_mode="HTML",
                   reply_markup=mk(("✅ Tasdiqlash (Soni -> 0)", f"ok:{key}:{cid}"), ("❌ Rad etish", f"no:{key}:{cid}"), w=2))
    bot.send_message(cid, X["thx"][i], parse_mode="HTML", reply_markup=kbd(l))

# ---------- Admin yordamchi funksiyalari ----------
def amain(c=None):
    kb = mk(("📊 Kunlik Savdo Hisobotini Chiqarish", "dy"), ("📥 Apparatga Mahsulot Qo'shish (+)", "as"),
            ("🔄 Yangi Kun Boshlash (Qoldiqlarni yangilash)", "rd"), ("📝 Narx va Sonini O'zgartirish / O'chirish", "sc"),
            ("➕ Yangi Mahsulot Qo'shish (Baza uchun)", "an"))
    t = "🛠 <b>ADMIN PANEL</b>\n\nKerakli bo'limni tanlang:"
    if c: bot.edit_message_text(t, c.message.chat.id, c.message.message_id, parse_mode="HTML", reply_markup=kb)
    else: snd(t, kb)

@bot.message_handler(commands=["admin", "setprice"])
def admin_cmd(m):
    if m.chat.id == ADMIN_ID: amain()

def report():
    """Qisqa hisobot: sotilgan mahsulotlar + jami soni va daromad."""
    tot = qty = 0; rows = []
    for it in PRODUCTS.values():
        sold = max(it.get("start_count", it["count"]) + it.get("added_today", 0) - it["count"], 0)
        if sold: rows.append(f"🔹 {html.escape(it['name_uz'])} — {sold} ta — {sold * it['price']:,} so'm"); qty += sold; tot += sold * it["price"]
    body = "\n".join(rows) if rows else "Bugun hali savdo bo'lmagan."
    return f"📊 <b>BUGUNGI SAVDO HISOBOTI:</b>\n\n{body}\n\n📦 <b>JAMI SOTILGAN TOVAR:</b> {qty} ta\n💰 <b>JAMI TUSHUM (SAVDO):</b> {tot:,} so'm"

def add_stock(m, k):
    if bad(m): return
    it = PRODUCTS.get(k)
    if not it: return amain()
    n = int(m.text); it["count"] += n; it["added_today"] += n; save()
    snd(f"✅ <code>{html.escape(it['name_uz'])}</code> ga +{n} ta qo'shildi! Hozirgi qoldiq: {it['count']} ta"); amain()

def upd(m, k, f):
    if bad(m, "Amal bekor qilindi."): return
    if k in PRODUCTS:
        PRODUCTS[k][f] = int(m.text); save(); n = html.escape(PRODUCTS[k]["name_uz"]); v = int(m.text)
        snd(f"✅ <code>{n}</code> narxi <b>{v:,} so'm</b>ga o'zgartirildi!" if f == "price"
            else f"✅ <code>{n}</code> soni <b>{v} ta</b> deb yangilandi!", HOME())

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
    n = int(m.text); nme = tmp["name"]
    PRODUCTS[f"item_{int(time.time())}"] = {"name_uz": nme, "name_ru": nme, "name_en": nme, "price": tmp["price"],
                                            "count": n, "start_count": n, "added_today": 0, "category": tmp["category"]}
    save()
    snd(f"🎉 <b>Yangi mahsulot qo'shildi!</b>\n\n📌 Nomi: {html.escape(nme)}\n📂 Bo'lim: {CATS[tmp['category']]}\n"
        f"💰 Narxi: {tmp['price']:,} so'm\n📊 Soni: {n} ta", HOME())

def reply_user(m, uid):
    try:
        bot.send_message(uid, f"💬 <b>Ma'muriyatdan javob / Response from support:</b>\n\n{html.escape(m.text)}", parse_mode="HTML")
        snd("✅ Javob foydalanuvchiga yetkazildi!")
    except Exception as e: snd(f"❌ Xatolik yuz berdi: {html.escape(str(e))}")

# ---------- Barcha tugmalar (callback) ----------
ADM = {"ok", "no", "am", "dy", "as", "sk", "ak", "rd", "sc", "ec", "ee", "dp", "cp", "cc", "an", "ac", "rp"}

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    a, *d = c.data.split(":"); k = d[0] if d else None
    cid, mid = c.message.chat.id, c.message.message_id
    l = user_lang.get(cid, "uz"); i = LI[l]
    ans = lambda t=None: bot.answer_callback_query(c.id, t, show_alert=bool(t))
    ed = lambda t, kb=None: bot.edit_message_text(t, cid, mid, parse_mode="HTML", reply_markup=kb)
    if a in ADM and cid != ADMIN_ID: return
    if a not in ("pd", "ok", "no", "rd"): ans()

    # --- mijoz ---
    if a == "sl":
        user_lang[cid] = k; bot.delete_message(cid, mid)
        bot.send_message(cid, X["chosen"][LI[k]], reply_markup=kbd(k))
    elif a == "mc": ed(X["selcat"][i], cats_kb(l))
    elif a == "bm": bot.delete_message(cid, mid)
    elif a == "dk": ed(X["seldrink"][i], mk(*[(X[x][i], f"ct:{x}") for x in DRINKS], (X["back"][i], "mc")))
    elif a == "ct":
        rows = [(f"🔹 {nm(it, l)}", f"pd:{x}") for x, it in PRODUCTS.items() if it["category"] == k]
        n = len(rows); rows.append((X["back"][i], "dk" if k in DRINKS else "mc"))
        ed(X["pick" if n else "empty"][i], mk(*rows))
    elif a == "pd":
        it = PRODUCTS.get(k)
        if not it: ans(X["nf"][i]); ed(X["selcat"][i], cats_kb(l))
        else:
            ans()
            ed(X["det"][i].format(n=html.escape(nm(it, l)), p=f"{it['price']:,}", c=it["count"]),
               mk((X["out"][i], f"os:{k}"), (X["backl"][i], f"ct:{it['category']}")))
    elif a == "os":
        if k in PRODUCTS: bot.register_next_step_handler(bot.send_message(cid, X["oos"][i], parse_mode="HTML"), oos_photo, k)

    # --- admin: tasdiqlash / rad etish ---
    elif a in ("ok", "no"):
        it = PRODUCTS.get(k); pn = html.escape(it["name_uz"]) if it else "Mahsulot"
        if a == "ok":
            if it: it["count"] = 0; save()
            cap, al = "\n\n<b>✅ ADMIN TAROFIDAN TASDIQLANDI!</b> Soni 0 ga tushirildi.", "✅ Mahsulot soni 0 deb saqlandi!"
        else: cap, al = "\n\n<b>❌ RAD ETILDI.</b> Mahsulot soni o'zgartirilmadi.", "❌ So'rov rad etildi."
        bot.edit_message_caption(c.message.html_caption + cap, cid, mid, parse_mode="HTML")
        ans(al)
        if a == "ok":
            try: bot.send_message(d[1], f"✅ <b>{pn}</b> bo'yicha yuborgan xabaringiz admin tomonidan tasdiqlandi. Rahmat!", parse_mode="HTML")
            except Exception: pass

    # --- admin: menyu, hisobot, yangi kun ---
    elif a == "am": amain(c)
    elif a == "dy": ed(report(), HOME("🏠 Admin Menyusi"))
    elif a == "rd":
        for it in PRODUCTS.values(): it["start_count"], it["added_today"] = it["count"], 0
        save(); ans("✅ Yangi kun boshlandi! Kunlik ko'rsatkichlar nolga tushirildi."); amain(c)

    # --- admin: kategoriya bo'yicha (Qo'shish "as/sk" va Tahrirlash "sc/ec") ---
    elif a in ("as", "sc"):
        st = a == "as"
        ed("📂 Qaysi bo'limdagi mahsulotga son qo'shmoqchisiz?" if st else "📂 Qaysi bo'limdagi mahsulotlarni tahrirlamoqchisiz?",
           main_kb("sk" if st else "ec", "🏠 Admin Menyusi" if st else "🏠 Admin menyusi"))
    elif a in ("sk", "ec"):
        st = a == "sk"; home = "🏠 Admin Menyusi" if st else "🏠 Admin menyusi"
        if k == "drinks": ed("🥤 Ichimlik turini tanlang:", sub_kb(a, "as" if st else "sc", home))
        else:
            rows = [(f"➕ {it['name_uz']} (Hozir: {it['count']} ta)" if st else f"⚙️ {it['name_uz']} ({it['price']} so'm | {it['count']} ta)",
                     f"{'ak' if st else 'ee'}:{x}") for x, it in PRODUCTS.items() if it["category"] == k]
            kb = mk(*rows, ("🔙 Ortga", f"{a}:drinks" if k in DRINKS else ("as" if st else "sc")), (home, "am"))
            if not rows: ed("Ushbu bo'limda mahsulot topilmadi." if st else "Ushbu bo'limda hozircha mahsulot yo'q.", kb)
            else: ed(f"📌 <b>{CATS[k]}</b> mahsulotlari:\n" + ("Soni oshiriladigan mahsulotni tanlang:" if st else "Tahrirlash yoki o'chirish uchun birini tanlang:"), kb)
    elif a == "ak":
        if k in PRODUCTS: ask(f"✍️ <code>{html.escape(PRODUCTS[k]['name_uz'])}</code> ga nechta dona qo'shdingiz? (masalan: 10):", add_stock, k)
    elif a == "ee":
        it = PRODUCTS.get(k)
        if not it: amain(c)
        else:
            ed(f"📌 <b>{html.escape(it['name_uz'])}</b> bo'yicha amalni tanlang:",
               mk(("💰 Narxni o'zgartirish", f"cp:{k}"), ("📊 Soni (Qoldiq)ni o'zgartirish", f"cc:{k}"),
                  ("🗑 Mahsulotni BUTUNLAY O'CHIRISH", f"dp:{k}"), ("🔙 Ortga (Ro'yxatga)", f"ec:{it['category']}"),
                  ("🏠 Admin menyusi", "am")))
    elif a == "dp":
        if k in PRODUCTS:
            it = PRODUCTS.pop(k); save()
            ed(f"🗑 <b>{html.escape(it['name_uz'])}</b> butunlay o'chirib tashlandi!",
               mk(("🔙 Ro'yxatga qaytish", f"ec:{it['category']}"), ("🏠 Admin menyusi", "am")))
        else: amain(c)
    elif a in ("cp", "cc"):
        if k not in PRODUCTS: amain(c)
        else:
            what = "<b>narxni</b>" if a == "cp" else "<b>soni (dona)</b>ni"
            ask(f"✍️ <code>{html.escape(PRODUCTS[k]['name_uz'])}</code> uchun yangi {what} kiriting:{BK}", upd, k, "price" if a == "cp" else "count")
    elif a == "an": ed("➕ Yangi mahsulot qaysi toifaga kiradi?", cat_kb("ac", "🍫 Sneklar"))
    elif a == "ac":
        tmp.clear(); tmp["category"] = k
        ask(f"✍️ <b>{CATS[k]}</b> uchun mahsulot nomini kiriting:{BK}", add_name)
    elif a == "rp": ask(f"✍️ Javobingizni yozing (ID: <code>{k}</code>):", reply_user, k)

# ---------- Ishga tushirish ----------
app = Flask(__name__)

@app.route("/")
def home(): return "Bot is running 24/7!"

def run_bot():
    try: bot.set_my_commands([T.BotCommand("start", "Botni qayta ishga tushirish / Restart bot 🔄")])
    except Exception as e: print(f"Buyruqlarni o'rnatishda xatolik: {e}")
    bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
