import os
import threading
from flask import Flask
import telebot
from telebot import types

TOKEN = '8664579659:AAG5pvP_8_PO4iJr9RUZpBDfrYX1TLEL6ug'
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8481771373
user_states = {}

# Flask сервер для работы на Render 24/7
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

# 1. Команда /start (возвращает только имя и меню)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_products = types.KeyboardButton("☕ Mahsulotlar va Narxlar")
    btn_lang = types.KeyboardButton("🌐 Tilni tanlash / Язык")
    btn_suggest = types.KeyboardButton("💡 Taklifim bor")
    btn_complaint = types.KeyboardButton("⚠️ Shikoyatim bor")
    
    keyboard.add(btn_products, btn_lang, btn_suggest, btn_complaint)
    
    bot.send_message(
        message.chat.id, 
        user_name, 
        reply_markup=keyboard
    )

# 2. Раздел "Mahsulotlar va Narxlar"
@bot.message_handler(func=lambda message: message.text == "☕ Mahsulotlar va Narxlar")
def show_products(message):
    products_text = (
        "📋 Bizning avtomatlardagi mahsulotlar va narxlar:\n\n"
        "☕ Issiq ichimliklar:\n"
        "• Espresso — 8 000 so'm\n"
        "• Americano — 10 000 so'm\n"
        "• Cappuccino — 12 000 so'm\n"
        "• Hot Chocolate — 12 000 so'm\n\n"
        "🍫 Snak va shirinliklar:\n"
        "• Snickers / KitKat — 10 000 so'm\n"
        "• Lays chipslari — 9 000 so'm\n"
        "• Gazlangan suvlar — 5 000 so'm\n\n"
        "📌 Narxlar barcha vending nuqtalarimizda bir xil!"
    )
    bot.send_message(message.chat.id, products_text)

# 3. Раздел выбора языка
@bot.message_handler(func=lambda message: message.text == "🌐 Tilni tanlash / Язык")
def choose_language(message):
    markup = types.InlineKeyboardMarkup()
    btn_uz = types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")
    btn_ru = types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    markup.add(btn_uz, btn_ru)
    
    bot.send_message(message.chat.id, "Muloqot tilini tanlang / Choose language:", reply_markup=markup)

# Обработчик выбора языка
@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    if call.data == "lang_uz":
        bot.answer_callback_query(call.id, "O'zbek tili tanlandi 🇺🇿")
        bot.send_message(call.message.chat.id, "Til o'zgartirildi: O'zbekcha 🇺🇿")
    elif call.data == "lang_ru":
        bot.answer_callback_query(call.id, "Выбран русский язык 🇷🇺")
        bot.send_message(call.message.chat.id, "Язык изменен: Русский 🇷🇺")

# 4. Обработка кнопок Предложений и Жалоб
@bot.message_handler(func=lambda message: message.text in ["💡 Taklifim bor", "⚠️ Shikoyatim bor"] and message.chat.id != ADMIN_ID)
def handle_choice(message):
    if message.text == "💡 Taklifim bor":
        user_states[message.chat.id] = "suggestion"
        bot.send_message(message.chat.id, "Ajoyib! Biz xizmatimizni yaxshilashdan doim mamnunmiz. Taklifingizni (matn, rasm yoki video) yozib yuboring:", reply_markup=types.ReplyKeyboardRemove())
    else:
        user_states[message.chat.id] = "complaint"
        bot.send_message(message.chat.id, "Noqulaylik uchun oldindan uzr so'raymiz. Shikoyatingiz tafsilotlarini yozib yuboring:", reply_markup=types.ReplyKeyboardRemove())

# 5. Прием сообщений от пользователей и отправка админу
@bot.message_handler(content_types=['text', 'photo', 'video'], func=lambda message: message.chat.id != ADMIN_ID)
def handle_user_content(message):
    user = message.from_user
    state = user_states.get(message.chat.id)
    
    if not state:
        bot.send_message(message.chat.id, "Iltimos, avval /start buyrug'ini bosing.")
        return

    category = "💡 TAKLIF" if state == "suggestion" else "⚠️ SHIKOYAT"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_{message.chat.id}"))

    user_info = f"📩 Yangi {category}!\n\nKimdan: @{user.username} ({user.first_name})\nID: {message.chat.id}"

    if message.content_type == 'text':
        bot.send_message(ADMIN_ID, f"{user_info}\n\nXabar: {message.text}", reply_markup=markup)
    elif message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"{user_info}\n\nIzoh: {message.caption or ''}", reply_markup=markup)
    elif message.content_type == 'video':
        bot.send_video(ADMIN_ID, message.video.file_id, caption=f"{user_info}\n\nIzoh: {message.caption or ''}", reply_markup=markup)

    if state == "suggestion":
        bot.send_message(
            message.chat.id, 
            "Fikr va taklifingiz uchun katta rahmat! 💡 Biz uni albatta sinchiklab o'rganib chiqamiz va xizmatimizni yanada yaxshilashga harakat qilamiz."
        )
    else:
        bot.send_message(
            message.chat.id, 
            "Murojaatingiz uchun rahmat! ⚠️ Yuzaga kelgan noqulaylik uchun chin dildan uzr so'raymiz. Shikoyatingizni albatta o'rganib chiqamiz."
        )
    
    user_states.pop(message.chat.id, None)

# 6. Функция ответа админа
@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def ask_admin_reply(call):
    target_user_id = call.data.split('_')[1]
    msg = bot.send_message(ADMIN_ID, f"✍️ Foydalanuvchiga yubormoqchi bo'lgan javobingizni yozing (ID: {target_user_id}):")
    bot.register_next_step_handler(msg, send_reply_to_user, target_user_id)

def send_reply_to_user(message, target_user_id):
    try:
        bot.send_message(target_user_id, f"💬 Ma'muriyatdan javob:\n\n{message.text}")
        bot.send_message(ADMIN_ID, "✅ Javob foydalanuvchiga muvaffaqiyatli yetkazildi!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Xatolik yuz berdi: {e}")

# Запуск бота в отдельном потоке
def run_bot():
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
