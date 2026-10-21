import os
import threading
from flask import Flask
import telebot
from telebot import types

TOKEN = '8664579659:AAG5pvP_8_PO4iJr9RUZpBDfrYX1TLEL6ug'
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8481771373

user_states = {}
user_lang = {}

# Mahsulotlar ombori
PRODUCTS = {
    "espresso": {"name_uz": "Espresso", "name_ru": "Эспрессо", "price": 8000, "count": 15, "category": "hot"},
    "americano": {"name_uz": "Americano", "name_ru": "Американо", "price": 10000, "count": 20, "category": "hot"},
    "cappuccino": {"name_uz": "Cappuccino", "name_ru": "Капучино", "price": 12000, "count": 12, "category": "hot"},
    "snickers": {"name_uz": "Snickers / KitKat", "name_ru": "Snickers / KitKat", "price": 10000, "count": 8, "category": "snack"},
    "lays": {"name_uz": "Lays chipslari", "name_ru": "Чипсы Lays", "price": 9000, "count": 5, "category": "snack"},
    "water": {"name_uz": "Gazlangan suvlar", "name_ru": "Газированные напитки", "price": 5000, "count": 30, "category": "water"}
}

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

# Asosiy menyu (ReplyKeyboard)
def get_main_keyboard(lang):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if lang == 'ru':
        btn_products = types.KeyboardButton("☕ Товары и Цены")
        btn_lang = types.KeyboardButton("🌐 Сменить язык")
        btn_suggest = types.KeyboardButton("💡 Есть предложение")
        btn_complaint = types.KeyboardButton("⚠️ Есть жалоба")
    else:
        btn_products = types.KeyboardButton("☕ Mahsulotlar va Narxlar")
        btn_lang = types.KeyboardButton("🌐 Tilni tanlash")
        btn_suggest = types.KeyboardButton("💡 Taklifim bor")
        btn_complaint = types.KeyboardButton("⚠️ Shikoyatim bor")
        
    keyboard.add(btn_products, btn_lang, btn_suggest, btn_complaint)
    return keyboard

# 1. /start - Salomlashish va Til tanlash
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_uz = types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="setlang_uz")
    btn_ru = types.InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang_ru")
    markup.add(btn_uz, btn_ru)
    
    user_name = message.from_user.first_name
    welcome_text = (
        f"Assalomu alaykum, {user_name}!\n"
        f"Bizning vending xizmatimiz botiga xush kelibsiz. Sizga qanday yordam bera olaman?\n\n"
        f"Iltimos, muloqot tilini tanlang:\n"
        f"Здравствуйте! Пожалуйста, выберите язык:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# Til tanlanganda
@bot.callback_query_handler(func=lambda call: call.data.startswith('setlang_'))
def handle_language_choice(call):
    lang = call.data.split('_')[1]
    user_lang[call.message.chat.id] = lang
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    text = "O'zbek tili tanlandi! 🇺🇿\nQuyidagi menyudan foydalanishingiz mumkin:" if lang == 'uz' else "Выбран русский язык! 🇷🇺\nВы можете использовать меню ниже:"
    bot.send_message(call.message.chat.id, text, reply_markup=get_main_keyboard(lang))

# 2. Kategoriyalar ko'rinishi
@bot.message_handler(func=lambda message: message.text in ["☕ Mahsulotlar va Narxlar", "☕ Товары и Цены"])
def show_categories(message):
    lang = user_lang.get(message.chat.id, 'uz')
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if lang == 'ru':
        markup.add(
            types.InlineKeyboardButton("☕ Горячие напитки", callback_data="cat_hot"),
            types.InlineKeyboardButton("🍫 Снеки и сладости", callback_data="cat_snack"),
            types.InlineKeyboardButton("🥤 Напитки и вода", callback_data="cat_water")
        )
        text = "📂 Выберите категорию товаров:"
    else:
        markup.add(
            types.InlineKeyboardButton("☕ Issiq ichimliklar", callback_data="cat_hot"),
            types.InlineKeyboardButton("🍫 Snek va shirinliklar", callback_data="cat_snack"),
            types.InlineKeyboardButton("🥤 Ichimliklar va suvlar", callback_data="cat_water")
        )
        text = "📂 Mahsulotlar bo'limini tanlang:"
        
    bot.send_message(message.chat.id, text, reply_markup=markup)

# Kategoriya tanlanganda mahsulotlar ro'yxati va "Ortga" tugmasi
@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def show_products_in_category(call):
    cat = call.data.split('_')[1]
    lang = user_lang.get(call.message.chat.id, 'uz')
    
    markup = types.InlineKeyboardMarkup()
    for key, item in PRODUCTS.items():
        if item["category"] == cat:
            name = item["name_ru"] if lang == 'ru' else item["name_uz"]
            markup.add(types.InlineKeyboardButton(f"{name}", callback_data=f"prod_{key}"))
            
    btn_back = types.InlineKeyboardButton("🔙 Ortga" if lang == 'uz' else "🔙 Назад", callback_data="back_to_cats")
    markup.add(btn_back)
            
    text = "Выберите товар:" if lang == 'ru' else "Mahsulotni tanlang:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# Mahsulot kartochkasi va "Ortga" tugmasi
@bot.callback_query_handler(func=lambda call: call.data.startswith('prod_'))
def show_product_details(call):
    prod_key = call.data.split('_')[1]
    lang = user_lang.get(call.message.chat.id, 'uz')
    item = PRODUCTS[prod_key]
    
    name = item["name_ru"] if lang == 'ru' else item["name_uz"]
    
    if lang == 'ru':
        text = f"📦 **Товар:** {name}\n💰 **Цена:** {item['price']:,} сум\n📊 **В наличии в аппарате:** {item['count']} шт."
        btn_out = types.InlineKeyboardButton("🚨 Сообщить: Товар закончился", callback_data=f"outofstock_{prod_key}")
        btn_back = types.InlineKeyboardButton("🔙 Ortga", callback_data=f"cat_{item['category']}")
    else:
        text = f"📦 **Mahsulot:** {name}\n💰 **Narxi:** {item['price']:,} so'm\n📊 **Qurilmada mavjud:** {item['count']} ta"
        btn_out = types.InlineKeyboardButton("🚨 Mahsulot tugadi (Xabar berish)", callback_data=f"outofstock_{prod_key}")
        btn_back = types.InlineKeyboardButton("🔙 Ortga", callback_data=f"cat_{item['category']}")
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(btn_out, btn_back)
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# Kategoriyalarga qaytish (Ortga)
@bot.callback_query_handler(func=lambda call: call.data == "back_to_cats")
def back_to_categories(call):
    lang = user_lang.get(call.message.chat.id, 'uz')
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if lang == 'ru':
        markup.add(
            types.InlineKeyboardButton("☕ Горячие напитки", callback_data="cat_hot"),
            types.InlineKeyboardButton("🍫 Снеки и сладости", callback_data="cat_snack"),
            types.InlineKeyboardButton("🥤 Напитки и вода", callback_data="cat_water")
        )
        text = "📂 Выберите категорию товаров:"
    else:
        markup.add(
            types.InlineKeyboardButton("☕ Issiq ichimliklar", callback_data="cat_hot"),
            types.InlineKeyboardButton("🍫 Snek va shirinliklar", callback_data="cat_snack"),
            types.InlineKeyboardButton("🥤 Ichimliklar va suvlar", callback_data="cat_water")
        )
        text = "📂 Mahsulotlar bo'limini tanlang:"
        
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# Mahsulot tugagani haqida xabar berish
@bot.callback_query_handler(func=lambda call: call.data.startswith('outofstock_'))
def report_out_of_stock(call):
    prod_key = call.data.split('_')[1]
    item = PRODUCTS[prod_key]
    user = call.from_user
    lang = user_lang.get(call.message.chat.id, 'uz')
    
    confirm_text = "Rahmat! Adminlarga mahsulot tugagani haqida xabar berildi." if lang == 'uz' else "Спасибо! Администратору отправлено уведомление."
    bot.answer_callback_query(call.id, confirm_text, show_alert=True)
    
    admin_alert = f"⚠️ **DIQQAT! MAHSULOT TUGADI!**\n\nFoydalanuvchi @{user.username} ({user.first_name}) quyidagi mahsulot tugaganini ma'lum qildi:\n📌 **{item['name_uz']}**"
    bot.send_message(ADMIN_ID, admin_alert, parse_mode="Markdown")

# Tilni qayta tanlash
@bot.message_handler(func=lambda message: message.text in ["🌐 Tilni tanlash", "🌐 Сменить язык"])
def change_language_menu(message):
    send_welcome(message)

# 3. ADMIN PANEL (`/admin`)
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID: return
    
    markup = types.InlineKeyboardMarkup()
    for key, item in PRODUCTS.items():
        markup.add(types.InlineKeyboardButton(f"⚙️ {item['name_uz']} ({item['price']} so'm | {item['count']} ta)", callback_data=f"adm_edit_{key}"))
        
    bot.send_message(ADMIN_ID, "🛠 **ADMIN PANEL**\n\nQaysi mahsulotni tahrirlamoqchisiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_'))
def admin_choose_option(call):
    if call.message.chat.id != ADMIN_ID: return
    prod_key = call.data.split('_')[2]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("💰 Narxni o'zgartirish", callback_data=f"change_p_{prod_key}"),
        types.InlineKeyboardButton("📊 Soni (Qoldiq)ni o'zgartirish", callback_data=f"change_c_{prod_key}")
    )
    bot.send_message(ADMIN_ID, f"📌 **{PRODUCTS[prod_key]['name_uz']}** bo'yicha nimani o'zgartirasiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('change_p_', 'change_c_')))
def admin_input_prompt(call):
    if call.message.chat.id != ADMIN_ID: return
    action, _, prod_key = call.data.split('_')
    
    if action == 'change':
        if call.data.startswith('change_p_'):
            msg = bot.send_message(ADMIN_ID, f"✍️ `{PRODUCTS[prod_key]['name_uz']}` uchun yangi **narxni** kiriting (masalan: 12000):")
            bot.register_next_step_handler(msg, update_price, prod_key)
        else:
            msg = bot.send_message(ADMIN_ID, f"✍️ `{PRODUCTS[prod_key]['name_uz']}` uchun yangi **soni (dona)**ni kiriting (masalan: 20):")
            bot.register_next_step_handler(msg, update_count, prod_key)

def update_price(message, prod_key):
    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Noto'g'ri qiymat! Faqat raqam kiriting.")
        return
    PRODUCTS[prod_key]['price'] = int(message.text)
    bot.send_message(ADMIN_ID, f"✅ `{PRODUCTS[prod_key]['name_uz']}` narxi **{int(message.text):,} so'm**ga o'zgartirildi!")

def update_count(message, prod_key):
    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Noto'g'ri qiymat! Faqat raqam kiriting.")
        return
    PRODUCTS[prod_key]['count'] = int(message.text)
    bot.send_message(ADMIN_ID, f"✅ `{PRODUCTS[prod_key]['name_uz']}` soni **{int(message.text)} ta** deb yangilandi!")

# 4. Taklif va Shikoyatlar
@bot.message_handler(func=lambda message: message.text in ["💡 Taklifim bor", "💡 Есть предложение", "⚠️ Shikoyatim bor", "⚠️ Есть жалоба"] and message.chat.id != ADMIN_ID)
def handle_choice(message):
    lang = user_lang.get(message.chat.id, 'uz')
    if "Taklif" in message.text or "предложение" in message.text:
        user_states[message.chat.id] = "suggestion"
        text = "Taklifingizni yozib yuboring:" if lang == 'uz' else "Напишите ваше предложение:"
    else:
        user_states[message.chat.id] = "complaint"
        text = "Shikoyatingiz tafsilotlarini yozib yuboring:" if lang == 'uz' else "Напишите подробности вашей жалобы:"
    bot.send_message(message.chat.id, text, reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(content_types=['text', 'photo', 'video'], func=lambda message: message.chat.id != ADMIN_ID)
def handle_user_content(message):
    lang = user_lang.get(message.chat.id, 'uz')
    state = user_states.get(message.chat.id)
    if not state:
        bot.send_message(message.chat.id, "Iltimos, avval /start buyrug'ini bosing.")
        return

    category = "💡 TAKLIF" if state == "suggestion" else "⚠️ SHIKOYAT"
    user = message.from_user
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_{message.chat.id}"))

    user_info = f"📩 Yangi {category}!\n\nKimdan: @{user.username} ({user.first_name})\nID: {message.chat.id}"

    if message.content_type == 'text':
        bot.send_message(ADMIN_ID, f"{user_info}\n\nXabar: {message.text}", reply_markup=markup)
    elif message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"{user_info}\n\nIzoh: {message.caption or ''}", reply_markup=markup)
    elif message.content_type == 'video':
        bot.send_video(ADMIN_ID, message.video.file_id, caption=f"{user_info}\n\nIzoh: {message.caption or ''}", reply_markup=markup)

    thanks_msg = "Rahmat! Murojaatingiz qabul qilindi." if lang == 'uz' else "Спасибо! Ваше обращение принято."
    bot.send_message(message.chat.id, thanks_msg, reply_markup=get_main_keyboard(lang))
    user_states.pop(message.chat.id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def ask_admin_reply(call):
    target_user_id = call.data.split('_')[1]
    msg = bot.send_message(ADMIN_ID, f"✍️ Javobingizni yozing (ID: {target_user_id}):")
    bot.register_next_step_handler(msg, send_reply_to_user, target_user_id)

def send_reply_to_user(message, target_user_id):
    try:
        bot.send_message(target_user_id, f"💬 Ma'muriyatdan javob / Ответ от администрации:\n\n{message.text}")
        bot.send_message(ADMIN_ID, "✅ Javob yetkazildi!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Xatolik: {e}")

def run_bot():
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
