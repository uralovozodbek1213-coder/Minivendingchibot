import os
import threading
from flask import Flask
import telebot
from telebot import types

TOKEN = '8664579659:AAG5pvP_8_PO4iJr9RUZpBDfrYX1TLEL6ug'
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8481771373

# Foydalanuvchi holatlari va tanlagan tillari
user_states = {}
user_lang = {}

# Mahsulotlar va ularning boshlang'ich narxlari (Admin buni Telegram'dan o'zgartira oladi)
PRODUCTS = {
    "espresso": {"name_uz": "Espresso", "name_ru": "Эспрессо", "price": 8000, "category": "hot"},
    "americano": {"name_uz": "Americano", "name_ru": "Американо", "price": 10000, "category": "hot"},
    "cappuccino": {"name_uz": "Cappuccino", "name_ru": "Капучино", "price": 12000, "category": "hot"},
    "hot_chocolate": {"name_uz": "Hot Chocolate", "name_ru": "Горячий шоколад", "price": 12000, "category": "hot"},
    "snickers": {"name_uz": "Snickers / KitKat", "name_ru": "Snickers / KitKat", "price": 10000, "category": "snack"},
    "lays": {"name_uz": "Lays chipslari", "name_ru": "Чипсы Lays", "price": 9000, "category": "snack"},
    "water": {"name_uz": "Gazlangan suvlar", "name_ru": "Газированные напитки", "price": 5000, "category": "snack"}
}

# Flask server (Render 24/7 ishlashi uchun)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

# Asosiy menyu tugmalarini chiqarish funksiyasi
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
    
    # Admin uchun maxsus narx o'zgartirish tugmasi
    return keyboard

# 1. /start - Birinchi kirganda TIL TANLASH
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_uz = types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="setlang_uz")
    btn_ru = types.InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang_ru")
    markup.add(btn_uz, btn_ru)
    
    user_name = message.from_user.first_name
    bot.send_message(
        message.chat.id, 
        f"Assalomu alaykum, {user_name}!\nIltimos, muloqot tilini tanlang:\n\nЗдравствуйте! Пожалуйста, выберите язык:", 
        reply_markup=markup
    )

# Til tanlanganda ishlaydigan qism
@bot.callback_query_handler(func=lambda call: call.data.startswith('setlang_'))
def handle_language_choice(call):
    lang = call.data.split('_')[1]
    user_lang[call.message.chat.id] = lang
    
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    if lang == 'uz':
        text = "O'zbek tili tanlandi! 🇺🇿\nQuyidagi menyudan foydalanishingiz mumkin:"
    else:
        text = "Выбран русский язык! 🇷🇺\nВы можете использовать меню ниже:"
        
    bot.send_message(call.message.chat.id, text, reply_markup=get_main_keyboard(lang))

# 2. Mahsulotlar va Narxlarni ko'rsatish
@bot.message_handler(func=lambda message: message.text in ["☕ Mahsulotlar va Narxlar", "☕ Товары и Цены"])
def show_products(message):
    lang = user_lang.get(message.chat.id, 'uz')
    
    if lang == 'ru':
        text = "📋 Товары и цены в наших автоматах:\n\n☕ Горячие напитки:\n"
        for key, item in PRODUCTS.items():
            if item["category"] == "hot":
                text += f"• {item['name_ru']} — {item['price']:,} сум\n"
        text += "\n🍫 Снеки и сладости:\n"
        for key, item in PRODUCTS.items():
            if item["category"] == "snack":
                text += f"• {item['name_ru']} — {item['price']:,} сум\n"
        text += "\n📌 Цены одинаковы во всех наших точках!"
    else:
        text = "📋 Avtomatlarimizdagi mahsulotlar va narxlar:\n\n☕ Issiq ichimliklar:\n"
        for key, item in PRODUCTS.items():
            if item["category"] == "hot":
                text += f"• {item['name_uz']} — {item['price']:,} so'm\n"
        text += "\n🍫 Snek va shirinliklar:\n"
        for key, item in PRODUCTS.items():
            if item["category"] == "snack":
                text += f"• {item['name_uz']} — {item['price']:,} so'm\n"
        text += "\n📌 Narxlar barcha vending nuqtalarimizda bir xil!"

    bot.send_message(message.chat.id, text)

# 3. Tilni qayta tanlash tugmasi
@bot.message_handler(func=lambda message: message.text in ["🌐 Tilni tanlash", "🌐 Сменить язык"])
def change_language_menu(message):
    send_welcome(message)

# 4. ADMIN UCHUN: NARXLARNI O'ZGARTIRISH (`/admin` yoki `/setprice`)
@bot.message_handler(commands=['setprice', 'admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")
        return

    markup = types.InlineKeyboardMarkup()
    for key, item in PRODUCTS.items():
        btn = types.InlineKeyboardButton(f"{item['name_uz']} ({item['price']} so'm)", callback_data=f"editprice_{key}")
        markup.add(btn)

    bot.send_message(ADMIN_ID, "⚙️ Qaysi mahsulot narxini o'zgartirmoqchisiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('editprice_'))
def ask_new_price(call):
    if call.message.chat.id != ADMIN_ID:
        return
    prod_key = call.data.split('_')[1]
    msg = bot.send_message(ADMIN_ID, f"✍️ `{PRODUCTS[prod_key]['name_uz']}` uchun yangi narxni faqat raqamlarda kiriting (masalan: 11000):")
    bot.register_next_step_handler(msg, update_product_price, prod_key)

def update_product_price(message, prod_key):
    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Noto'g'ri narx! Faqat raqam kiriting (masalan: 10000). Qaytadan `/admin` bosing.")
        return
    
    new_price = int(message.text)
    PRODUCTS[prod_key]['price'] = new_price
    bot.send_message(ADMIN_ID, f"✅ `{PRODUCTS[prod_key]['name_uz']}` narxi **{new_price:,} so'm** qilib o'zgartirildi!\n\nEndi barcha foydalanuvchilar yangi narxni ko'rishadi.")

# 5. Taklif va Shikoyatlar
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

def run_bot():
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
