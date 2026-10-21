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
admin_temp_data = {}  # Yangi mahsulot qo'shish uchun vaqtincha xotira

# Mahsulotlar ombori
PRODUCTS = {
    "snickers": {"name_uz": "Snickers / KitKat", "name_ru": "Snickers / KitKat", "price": 10000, "count": 8, "category": "snack"},
    "lays": {"name_uz": "Lays chipslari", "name_ru": "Чипсы Lays", "price": 9000, "count": 5, "category": "snack"},
    "water": {"name_uz": "Gazlangan suvlar", "name_ru": "Газированные напитки", "price": 5000, "count": 30, "category": "water"}
}

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

# Asosiy menyu
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

# 2. Mahsulotlar kategoriyasi
@bot.message_handler(func=lambda message: message.text in ["☕ Mahsulotlar va Narxlar", "☕ Товары и Цены"])
def show_categories(message):
    lang = user_lang.get(message.chat.id, 'uz')
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if lang == 'ru':
        markup.add(
            types.InlineKeyboardButton("🍫 Снеки и сладости", callback_data="cat_snack"),
            types.InlineKeyboardButton("🥤 Напитки и вода", callback_data="cat_water"),
            types.InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
        )
        text = "📂 Выберите категорию товаров:"
    else:
        markup.add(
            types.InlineKeyboardButton("🍫 Snek va shirinliklar", callback_data="cat_snack"),
            types.InlineKeyboardButton("🥤 Ichimliklar va suvlar", callback_data="cat_water"),
            types.InlineKeyboardButton("🔙 Asosiy menyu", callback_data="back_to_main")
        )
        text = "📂 Mahsulotlar bo'limini tanlang:"
        
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def show_products_in_category(call):
    cat = call.data.split('_')[1]
    lang = user_lang.get(call.message.chat.id, 'uz')
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, item in PRODUCTS.items():
        if item["category"] == cat:
            name = item["name_ru"] if lang == 'ru' else item["name_uz"]
            markup.add(types.InlineKeyboardButton(f"{name}", callback_data=f"prod_{key}"))
            
    btn_back = types.InlineKeyboardButton("🔙 Ortga" if lang == 'uz' else "🔙 Назад", callback_data="back_to_cats")
    markup.add(btn_back)
            
    text = "Выберите товар:" if lang == 'ru' else "Mahsulotni tanlang:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('prod_'))
def show_product_details(call):
    prod_key = call.data.split('_')[1]
    lang = user_lang.get(call.message.chat.id, 'uz')
    item = PRODUCTS[prod_key]
    
    name = item["name_ru"] if lang == 'ru' else item["name_uz"]
    
    if lang == 'ru':
        text = f"📦 **Товар:** {name}\n💰 **Цена:** {item['price']:,} сум\n📊 **В наличии в аппарате:** {item['count']} шт."
        btn_out = types.InlineKeyboardButton("🚨 Сообщить: Товар закончился", callback_data=f"outofstock_{prod_key}")
        btn_back = types.InlineKeyboardButton("🔙 Назад к списку", callback_data=f"cat_{item['category']}")
    else:
        text = f"📦 **Mahsulot:** {name}\n💰 **Narxi:** {item['price']:,} so'm\n📊 **Qurilmada mavjud:** {item['count']} ta"
        btn_out = types.InlineKeyboardButton("🚨 Mahsulot tugadi (Xabar berish)", callback_data=f"outofstock_{prod_key}")
        btn_back = types.InlineKeyboardButton("🔙 Ortga", callback_data=f"cat_{item['category']}")
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(btn_out, btn_back)
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_cats")
def back_to_categories(call):
    lang = user_lang.get(call.message.chat.id, 'uz')
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if lang == 'ru':
        markup.add(
            types.InlineKeyboardButton("🍫 Снеки и сладости", callback_data="cat_snack"),
            types.InlineKeyboardButton("🥤 Напитки и вода", callback_data="cat_water"),
            types.InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
        )
        text = "📂 Выберите категорию товаров:"
    else:
        markup.add(
            types.InlineKeyboardButton("🍫 Snek va shirinliklar", callback_data="cat_snack"),
            types.InlineKeyboardButton("🥤 Ichimliklar va suvlar", callback_data="cat_water"),
            types.InlineKeyboardButton("🔙 Asosiy menyu", callback_data="back_to_main")
        )
        text = "📂 Mahsulotlar bo'limini tanlang:"
        
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_menu(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

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

@bot.message_handler(func=lambda message: message.text in ["🌐 Tilni tanlash", "🌐 Сменить язык"])
def change_language_menu(message):
    send_welcome(message)

# 3. TAKLIFLAR
@bot.message_handler(func=lambda message: message.text in ["💡 Taklifim bor", "💡 Есть предложение"])
def handle_suggestion_button(message):
    lang = user_lang.get(message.chat.id, 'uz')
    msg_text = "Taklifingiz bo'lsa yozib yuboring:" if lang == 'uz' else "Напишите ваше предложение:"
    msg = bot.send_message(message.chat.id, msg_text)
    bot.register_next_step_handler(msg, process_suggestion)

def process_suggestion(message):
    lang = user_lang.get(message.chat.id, 'uz')
    user = message.from_user
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_{message.chat.id}"))
    
    user_info = f"💡 **YANGI TAKLIF!**\n\nKimdan: @{user.username or 'username_yoq'} ({user.first_name})\nID: {message.chat.id}"
    
    if message.content_type == 'text':
        bot.send_message(ADMIN_ID, f"{user_info}\n\nTaklif: {message.text}", reply_markup=markup)
    elif message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"{user_info}\n\nIzoh: {message.caption or ''}", reply_markup=markup)
        
    thanks_msg = "Rahmat, taklifingiz uchun! Albatta e'tibor beramiz." if lang == 'uz' else "Спасибо за ваше предложение! Мы обязательно обратим внимание."
    bot.send_message(message.chat.id, thanks_msg, reply_markup=get_main_keyboard(lang))

# 4. SHIKOYATLAR
@bot.message_handler(func=lambda message: message.text in ["⚠️ Shikoyatim bor", "⚠️ Есть жалоба"])
def handle_complaint_button(message):
    lang = user_lang.get(message.chat.id, 'uz')
    msg_text = "Shikoyatingiz yoki e'tirozingiz bo'lsa yozib yuboring:" if lang == 'uz' else "Напишите подробности вашей жалобы:"
    msg = bot.send_message(message.chat.id, msg_text)
    bot.register_next_step_handler(msg, process_complaint)

def process_complaint(message):
    lang = user_lang.get(message.chat.id, 'uz')
    user = message.from_user
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_{message.chat.id}"))
    
    user_info = f"⚠️ **YANGI SHIKOYAT!**\n\nKimdan: @{user.username or 'username_yoq'} ({user.first_name})\nID: {message.chat.id}"
    
    if message.content_type == 'text':
        bot.send_message(ADMIN_ID, f"{user_info}\n\nShikoyat: {message.text}", reply_markup=markup)
    elif message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"{user_info}\n\nIzoh: {message.caption or ''}", reply_markup=markup)
        
    thanks_msg = "Rahmat, e'tirozingiz uchun! Kamchilikni tezda bartaraf etamiz." if lang == 'uz' else "Спасибо за обращение! Мы быстро устраним проблему."
    bot.send_message(message.chat.id, thanks_msg, reply_markup=get_main_keyboard(lang))

# 5. MUKAMMAL ADMIN PANEL (/admin)
@bot.message_handler(commands=['admin', 'setprice'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📝 Narx va sonini o'zgartirish", callback_data="admin_edit_existing"),
        types.InlineKeyboardButton("➕ Yangi mahsulot qo'shish", callback_data="admin_add_new")
    )
    bot.send_message(ADMIN_ID, "🛠 **ADMIN PANEL**\n\nNimani amalga oshirmoqchisiz?", reply_markup=markup)

# 5.1. Mavjud mahsulotlarni tahrirlash bo'limi
@bot.callback_query_handler(func=lambda call: call.data == "admin_edit_existing")
def admin_show_products(call):
    if call.message.chat.id != ADMIN_ID: return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, item in PRODUCTS.items():
        markup.add(types.InlineKeyboardButton(f"⚙️ {item['name_uz']} ({item['price']} so'm | {item['count']} ta)", callback_data=f"adm_edit_{key}"))
        
    bot.send_message(ADMIN_ID, "Qaysi mahsulotni tahrirlamoqchisiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_'))
def admin_choose_option(call):
    if call.message.chat.id != ADMIN_ID: return
    prod_key = call.data.split('_')[2]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💰 Narxni o'zgartirish", callback_data=f"changep_{prod_key}"),
        types.InlineKeyboardButton("📊 Soni (Qoldiq)ni o'zgartirish", callback_data=f"changec_{prod_key}")
    )
    bot.send_message(ADMIN_ID, f"📌 **{PRODUCTS[prod_key]['name_uz']}** bo'yicha nimani o'zgartirasiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('changep_', 'changec_')))
def admin_input_prompt(call):
    if call.message.chat.id != ADMIN_ID: return
    action, prod_key = call.data.split('_')
    
    if action == 'changep':
        msg = bot.send_message(ADMIN_ID, f"✍️ `{PRODUCTS[prod_key]['name_uz']}` uchun yangi **narxni** kiriting (masalan: 12000):")
        bot.register_next_step_handler(msg, update_price, prod_key)
    elif action == 'changec':
        msg = bot.send_message(ADMIN_ID, f"✍️ `{PRODUCTS[prod_key]['name_uz']}` uchun yangi **soni (dona)**ni kiriting (masalan: 20):")
        bot.register_next_step_handler(msg, update_count, prod_key)

def update_price(message, prod_key):
    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Noto'g'ri qiymat! Faqat raqam kiriting. Qayta urinish uchun `/admin` bosing.")
        return
    PRODUCTS[prod_key]['price'] = int(message.text)
    bot.send_message(ADMIN_ID, f"✅ `{PRODUCTS[prod_key]['name_uz']}` narxi **{int(message.text):,} so'm**ga o'zgartirildi!")

def update_count(message, prod_key):
    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Noto'g'ri qiymat! Faqat raqam kiriting. Qayta urinish uchun `/admin` bosing.")
        return
    PRODUCTS[prod_key]['count'] = int(message.text)
    bot.send_message(ADMIN_ID, f"✅ `{PRODUCTS[prod_key]['name_uz']}` soni **{int(message.text)} ta** deb yangilandi!")

# 5.2. Yangi mahsulot qo'shish bo'limi
@bot.callback_query_handler(func=lambda call: call.data == "admin_add_new")
def admin_add_new_start(call):
    if call.message.chat.id != ADMIN_ID: return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🍫 Sneklar", callback_data="addcat_snack"),
        types.InlineKeyboardButton("🥤 Ichimliklar", callback_data="addcat_water")
    )
    bot.send_message(ADMIN_ID, "➕ Yangi mahsulot qaysi toifaga kiradi?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('addcat_'))
def admin_add_get_category(call):
    if call.message.chat.id != ADMIN_ID: return
    cat = call.data.split('_')[1]
    admin_temp_data[ADMIN_ID] = {"category": cat}
    
    msg = bot.send_message(ADMIN_ID, "✍️ Yangi mahsulot **nomini** kiriting (masalan: Mars shokoladi):")
    bot.register_next_step_handler(msg, admin_add_get_name)

def admin_add_get_name(message):
    admin_temp_data[ADMIN_ID]["name"] = message.text
    msg = bot.send_message(ADMIN_ID, f"✍️ `{message.text}` uchun **narxni** faqat raqamda kiriting (masalan: 11000):")
    bot.register_next_step_handler(msg, admin_add_get_price)

def admin_add_get_price(message):
    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Noto'g'ri narx! Qaytadan `/admin` deb yozib urinib ko'ring.")
        return
    admin_temp_data[ADMIN_ID]["price"] = int(message.text)
    msg = bot.send_message(ADMIN_ID, f"✍️ Apparatga bu mahsulotdan **nechta (dona)** qo'yildingiz? (masalan: 10):")
    bot.register_next_step_handler(msg, admin_add_finish)

def admin_add_finish(message):
    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Noto'g'ri son! Qaytadan `/admin` deb yozib urinib ko'ring.")
        return
    
    count = int(message.text)
    data = admin_temp_data[ADMIN_ID]
    
    # Kalit hosil qilish (id)
    new_key = f"prod_{len(PRODUCTS) + 1}"
    
    PRODUCTS[new_key] = {
        "name_uz": data["name"],
        "name_ru": data["name"],
        "price": data["price"],
        "count": count,
        "category": data["category"]
    }
    
    bot.send_message(
        ADMIN_ID, 
        f"🎉 **Yangi mahsulot qo'shildi!**\n\n📌 Nomi: {data['name']}\n💰 Narxi: {data['price']:,} so'm\n📊 Soni: {count} ta"
    )

# Admin javob berishi
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

import time

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)
        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

