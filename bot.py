import os, json, time, html, threading
from flask import Flask
import telebot
from telebot import types as T

bot = telebot.TeleBot(os.environ.get("TOKEN", "8664579659:AAG5pvP_8_PO4iJr9RUZpBDfrYX1TLEL6ug"))
ADMIN = int(os.environ.get("ADMIN_ID", 8481771373))
F = "products.json"
CATS = {"snack": "🍫 Snek", "energy": "⚡ Energetik", "carbonated": "🥤 Gazlangan", "still": "💧 Gazlanmagan"}

TX = {
    "uz": dict(menu="☕ Mahsulotlar", lang="🌐 Til", sug="💡 Taklif", comp="⚠️ Shikoyat", cat="Bo'limni tanlang:",
               prod="Mahsulotni tanlang:", back="🔙 Ortga", out="🚨 Mahsulot tugadi", price="Narxi", cnt="Mavjud",
               photo="📸 Tugaganini tasdiqlovchi rasm yuboring:", write="✍️ Yozing (matn yoki rasm):",
               thanks="🌟 Rahmat! Adminga yetkazildi.", ok="✅ Menyu:"),
    "ru": dict(menu="☕ Товары", lang="🌐 Язык", sug="💡 Предложение", comp="⚠️ Жалоба", cat="Выберите категорию:",
               prod="Выберите товар:", back="🔙 Назад", out="🚨 Товар закончился", price="Цена", cnt="В наличии",
               photo="📸 Отправьте фото, подтверждающее, что товар закончился:", write="✍️ Напишите (текст или фото):",
               thanks="🌟 Спасибо! Отправлено администратору.", ok="✅ Меню:"),
    "en": dict(menu="☕ Products", lang="🌐 Language", sug="💡 Suggestion", comp="⚠️ Complaint", cat="Select category:",
               prod="Select product:", back="🔙 Back", out="🚨 Out of stock", price="Price", cnt="In stock",
               photo="📸 Send a photo confirming it's out of stock:", write="✍️ Write (text or photo):",
               thanks="🌟 Thanks! Sent to the admin.", ok="✅ Menu:"),
}
BTN = {v[k]: k for v in TX.values() for k in ("menu", "lang", "sug", "comp")}

if os.path.exists(F):
    P = json.load(open(F, encoding="utf-8"))
else:
    P = {"redbull": {"name": "Red Bull 0.25L", "price": 18000, "count": 10, "category": "energy"},
         "pepsi": {"name": "Pepsi 0.5L", "price": 9000, "count": 15, "category": "carbonated"},
         "snickers": {"name": "Snickers", "price": 10000, "count": 8, "category": "snack"}}
L = {}
SF = "stats.json"
S = json.load(open(SF, encoding="utf-8")) if os.path.exists(SF) else {"day": None, "hist": []}
def sv(): json.dump(S, open(SF, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
def today(): return time.strftime("%Y-%m-%d", time.gmtime(time.time() + 5 * 3600))
def rn(i): return i.get("name") or i["name_uz"]
def AM(): return mk(("🌅 Kun boshi", "ds"), ("➕ Kirim (qo'shimcha)", "dk"), ("🌙 Kun oxiri / Hisobot", "de"),
                    ("📝 Tahrirlash / O'chirish", "ae"), ("➕ Yangi mahsulot", "aa"))

def save(): json.dump(P, open(F, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
def t(cid): return TX[L.get(cid, "uz")]
def nm(i): return html.escape(i.get("name") or i["name_uz"])
def mk(*b):
    m = T.InlineKeyboardMarkup(row_width=1)
    m.add(*[T.InlineKeyboardButton(a, callback_data=d) for a, d in b])
    return m
def cats(prefix): return mk(*[(v, f"{prefix}:{k}") for k, v in CATS.items()], ("🏠 Admin", "adm"))
def ask(text, fn, *a): bot.register_next_step_handler(bot.send_message(ADMIN, text), fn, *a)

@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id, "🌐 Til / Язык / Language:",
                     reply_markup=mk(("🇺🇿 O'zbekcha", "lang:uz"), ("🇷🇺 Русский", "lang:ru"), ("🇬🇧 English", "lang:en")))

@bot.message_handler(commands=["admin"])
def admin(m):
    if m.chat.id == ADMIN:
        bot.send_message(ADMIN, "🛠 ADMIN", reply_markup=AM())

@bot.message_handler(func=lambda m: m.text in BTN)
def buttons(m):
    k, tx = BTN[m.text], t(m.chat.id)
    if k == "menu": bot.send_message(m.chat.id, tx["cat"], reply_markup=mk(*[(v, f"cat:{c}") for c, v in CATS.items()]))
    elif k == "lang": start(m)
    else: bot.register_next_step_handler(bot.send_message(m.chat.id, tx["write"]), fwd, k)

def fwd(m, kind):
    u = m.from_user
    bot.send_message(ADMIN, f"{'💡' if kind == 'sug' else '⚠️'} @{u.username} {html.escape(u.first_name or '')} <code>{m.chat.id}</code>", parse_mode="HTML")
    bot.copy_message(ADMIN, m.chat.id, m.message_id, reply_markup=mk(("💬 Javob", f"reply:{m.chat.id}")))
    bot.send_message(m.chat.id, t(m.chat.id)["thanks"])

def got_photo(m, key):
    if m.content_type != "photo":
        return bot.register_next_step_handler(bot.send_message(m.chat.id, t(m.chat.id)["photo"]), got_photo, key)
    u = m.from_user
    bot.send_photo(ADMIN, m.photo[-1].file_id, caption=f"🚨 {P[key].get('name') or P[key]['name_uz']}\n@{u.username} ({m.chat.id})",
                   reply_markup=mk(("✅ Soni → 0", f"ok:{key}:{m.chat.id}"), ("❌ Rad etish", f"no:{key}:{m.chat.id}")))
    bot.send_message(m.chat.id, t(m.chat.id)["thanks"])

def setf(m, key, f):
    if m.text and m.text.isdigit() and key in P:
        P[key][f] = int(m.text); save(); bot.send_message(ADMIN, "✅ OK")
    else: bot.send_message(ADMIN, "❌ Raqam kiriting")

def addp(m, cat):
    try:
        n, p, c = [x.strip() for x in m.text.split("|")]
        P[f"item_{int(time.time())}"] = {"name": n, "price": int(p), "count": int(c), "category": cat}
        save(); bot.send_message(ADMIN, "✅ Qo'shildi")
    except Exception: bot.send_message(ADMIN, "❌ Format: Nomi|narx|soni")

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    d = c.data.split(":"); a = d[0]; cid, mid = c.message.chat.id, c.message.message_id; tx = t(cid)
    edit = lambda text, kb=None, **k: bot.edit_message_text(text, cid, mid, reply_markup=kb, **k)
    bot.answer_callback_query(c.id)
    if a == "lang":
        L[cid] = d[1]; bot.delete_message(cid, mid)
        k = T.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2); k.add(*[TX[d[1]][x] for x in ("menu", "lang", "sug", "comp")])
        bot.send_message(cid, TX[d[1]]["ok"], reply_markup=k)
    elif a == "menu": edit(tx["cat"], mk(*[(v, f"cat:{k}") for k, v in CATS.items()]))
    elif a == "cat":
        it = [(f"🔹 {nm(i)}", f"prod:{k}") for k, i in P.items() if i["category"] == d[1]]
        edit(tx["prod"], mk(*it, (tx["back"], "menu")))
    elif a == "prod" and d[1] in P:
        i = P[d[1]]
        edit(f"📦 <b>{nm(i)}</b>\n💰 {tx['price']}: {i['price']:,}\n📊 {tx['cnt']}: {i['count']}",
             mk((tx["out"], f"out:{d[1]}"), (tx["back"], f"cat:{i['category']}")), parse_mode="HTML")
    elif a == "out" and d[1] in P:
        bot.register_next_step_handler(bot.send_message(cid, tx["photo"]), got_photo, d[1])
    elif a == "reply": ask("✍️ Javob:", lambda m, u: bot.send_message(u, "💬 " + m.text), d[1])
    elif cid != ADMIN: return
    elif a in ("ok", "no"):
        if a == "ok" and d[1] in P: P[d[1]]["count"] = 0; save()
        bot.edit_message_caption(c.message.caption + ("\n\n✅ Tasdiqlandi" if a == "ok" else "\n\n❌ Rad etildi"), cid, mid)
        try: bot.send_message(int(d[2]), "✅" if a == "ok" else "ℹ️")
        except Exception: pass
    elif a == "adm": edit("🛠 ADMIN", AM())
    elif a == "ds":
        S["day"] = {"date": today(), "open": {k: i["count"] for k, i in P.items()}, "added": {}}; sv()
        edit(f"🌅 Kun boshlandi: {today()}\n\n" + "\n".join(f"{rn(i)}: {i['count']} ta" for i in P.values()), mk(("🏠 Admin", "adm")))
    elif a == "dk":
        if not S["day"]: edit("⚠️ Avval «Kun boshi» ni bosing.", mk(("🏠 Admin", "adm")))
        else: edit("Qaysi bo'limga kirim?", cats("dl"))
    elif a == "dl":
        edit("Mahsulot:", mk(*[(f"{rn(i)} ({i['count']})", f"dm:{k}") for k, i in P.items() if i["category"] == d[1]], ("🔙", "dk")))
    elif a == "dm" and d[1] in P: ask(f"➕ {rn(P[d[1]])}: nechta qo'shildi?", addq, d[1])
    elif a == "de":
        if not S["day"]: edit("⚠️ Avval «Kun boshi» ni bosing.", mk(("🏠 Admin", "adm")))
        else: edit("🌙 Kun oxiri: qoldiqlarni kiriting."); close_ask(list(P), {})
    elif a == "ae": edit("Bo'lim:", cats("al"))
    elif a == "aa": edit("Bo'lim:", cats("ac"))
    elif a == "al":
        edit("Tanlang:", mk(*[(f"⚙️ {nm(i)} ({i['price']} | {i['count']})", f"ao:{k}") for k, i in P.items() if i["category"] == d[1]], ("🔙", "ae")))
    elif a == "ao" and d[1] in P:
        edit(nm(P[d[1]]), mk(("💰 Narx", f"ap:{d[1]}"), ("📊 Soni", f"an:{d[1]}"), ("🗑 O'chirish", f"ad:{d[1]}"), ("🔙", f"al:{P[d[1]]['category']}")), parse_mode="HTML")
    elif a == "ap": ask("Yangi narx:", setf, d[1], "price")
    elif a == "an": ask("Yangi soni:", setf, d[1], "count")
    elif a == "ad": P.pop(d[1], None); save(); edit("🗑 O'chirildi", mk(("🏠 Admin", "adm")))
    elif a == "ac": ask("Nomi|narx|soni  (masalan: Pepsi 0.5L|9000|15)", addp, d[1])

def addq(m, key):
    if m.text and m.text.isdigit() and key in P:
        q = int(m.text); P[key]["count"] += q
        a = S["day"]["added"]; a[key] = a.get(key, 0) + q
        save(); sv(); bot.send_message(ADMIN, f"✅ +{q}. Hozir: {P[key]['count']} ta", reply_markup=mk(("➕ Yana kirim", "dk"), ("🏠 Admin", "adm")))
    else: bot.send_message(ADMIN, "❌ Raqam kiriting")

def close_ask(keys, res):
    if keys: ask(f"🌙 {rn(P[keys[0]])}: qoldiq nechta? (hisobda: {P[keys[0]]['count']})", close_got, keys, res)
    else: finish(res)

def close_got(m, keys, res):
    if not (m.text and m.text.isdigit()): return ask("❌ Raqam kiriting:", close_got, keys, res)
    res[keys[0]] = int(m.text); close_ask(keys[1:], res)

def finish(res):
    D = S["day"]; lines = []; tot = qty = 0
    for k, c in res.items():
        i = P[k]; o = D["open"].get(k, 0); a = D["added"].get(k, 0); s = o + a - c
        i["count"] = c; tot += s * i["price"]; qty += s
        if s or a or o: lines.append(f"• {rn(i)}: {o} + {a} − {c} = {s} ta × {i['price']:,} = {s * i['price']:,}" + (" ⚠️" if s < 0 else ""))
    S["hist"].append({"date": D["date"], "sold": qty, "sum": tot}); S["day"] = None; save(); sv()
    bot.send_message(ADMIN, f"📊 HISOBOT {D['date']}\n(boshida + kirim − oxirida = sotildi)\n\n" + "\n".join(lines) +
                     f"\n\n🛒 Jami sotildi: {qty} ta\n💰 Savdo: {tot:,} so'm", reply_markup=mk(("🏠 Admin", "adm")))

app = Flask(__name__)
@app.route("/")
def home(): return "Bot is running!"

if __name__ == "__main__":
    threading.Thread(target=lambda: bot.infinity_polling(skip_pending=True), daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
