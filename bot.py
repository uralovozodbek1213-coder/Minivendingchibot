import telebot
from telebot import types

TOKEN = '8664579659:AAG5pvP_8_PO4iJr9RUZpBDfrYX1TLEL6ug'
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8481771373
user_states = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton("💡 Taklifim bor"), types.KeyboardButton("⚠️ Shikoyatim bor"))
    
    bot.send_message(
        message.chat.id, 
        f"Assalomu alaykum, {user_name}! 🌟\nBizning vending xizmatimiz botiga xush kelibsiz. Sizga qanday yordam bera olaman?", 
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: message.text in ["💡 Taklifim bor", "⚠️ Shikoyatim bor"] and message.chat.id != ADMIN_ID)
def handle_choice(message):
    if message.text == "💡 Taklifim bor":
        user_states[message.chat.id] = "suggestion"
        bot.send_message(message.chat.id, "Ajoyib! Biz xizmatimizni yaxshilashdan doim mamnunmiz. Taklifingizni (matn, rasm yoki video) yozib yuboring:", reply_markup=types.ReplyKeyboardRemove())
    else:
        user_states[message.chat.id] = "complaint"
        bot.send_message(message.chat.id, "Noqulaylik uchun oldindan uzr so'raymiz. Shikoyatingiz tafsilotlarini yozib yuboring:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(content_types=['text', 'photo', 'video'], func=lambda message: message.chat.id != ADMIN_ID)
def handle_user_content(message):
    user = message.from_user
    state = user_states.get(message.chat.id)
    
    if not state:
        bot.send_message(message.chat.id, "Iltimos, avval /start buyrug'ini bosing.")
        return

    category = "💡 TAKLIF" if state == "suggestion" else "⚠️ SHIKOYAT"
    
    # Admin uchun inline tugma
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_{message.chat.id}"))

    user_info = f"📩 Yangi {category}!\n\nKimdan: @{user.username} ({user.first_name})\nID: {message.chat.id}"

    # Adminga yuborish
    if message.content_type == 'text':
        bot.send_message(ADMIN_ID, f"{user_info}\n\nXabar: {message.text}", reply_markup=markup)
    elif message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"{user_info}\n\nIzoh: {message.caption or ''}", reply_markup=markup)
    elif message.content_type == 'video':
        bot.send_video(ADMIN_ID, message.video.file_id, caption=f"{user_info}\n\nIzoh: {message.caption or ''}", reply_markup=markup)

    # Mijozga yuboriladigan chiroyli javoblar
    if state == "suggestion":
        bot.send_message(
            message.chat.id, 
            "Fikr va taklifingiz uchun katta rahmat! 💡 "
            "Biz uni albatta sinchiklab o'rganib chiqamiz va xizmatimizni yanada yaxshilashga harakat qilamiz. "
            "Sizning fikringiz biz uchun juda muhim! 🤝"
        )
    else:
        bot.send_message(
            message.chat.id, 
            "Murojaatingiz uchun rahmat! ⚠️ Yuzaga kelgan noqulaylik uchun chin dildan uzr so'raymiz. "
            "Shikoyatingizni albatta o'rganib chiqamiz va tez fursatda kerakli o'zgartirishlarni kiritamiz. "
            "Ishonchingiz uchun rahmat! 🙏"
        )
    
    user_states.pop(message.chat.id, None)

# Admin javob berish tugmasini bosganda
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

print("Bot ishga tushdi...")
bot.infinity_polling()
