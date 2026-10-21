import os
import time
import json
import threading
import html
from flask import Flask
import telebot
from telebot import types

TOKEN = '8664579659:AAG5pvP_8_PO4iJr9RUZpBDfrYX1TLEL6ug'
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8481771373

user_states = {}
user_lang = {}
admin_temp_data = {}

SUB_CATEGORIES = {
    "snack": "🍫 Sneklar va shirinliklar",
    "energy": "⚡ Energetik ichimliklar",
    "carbonated": "🥤 Gazlangan ichimliklar",
    "still": "💧 Gazlanmagan ichimliklar"
}

DATA_FILE = "products.json"

def load_products():
    if not os.path.exists(DATA_FILE):
        default_products = {
            "redbull": {"name_uz": "Red Bull 0.25L", "name_ru": "Red Bull 0.25Л", "name_en": "Red Bull 0.25L", "price": 18000, "count": 10, "category": "energy"},
            "flash": {"name_uz": "Flash Up 0.45L", "name_ru": "Flash Up 0.45Л", "name_en": "Flash Up 0.45L", "price": 8000, "count": 15, "category": "energy"},
            "pepsi": {"name_uz": "Pepsi 0.5L", "name_ru": "Пепси 0.5Л", "name_en": "Pepsi 0.5L", "price": 9000, "count": 15, "category": "carbonated"},
            "snickers": {"name_uz": "Snickers", "name_ru": "Snickers", "name_en": "Snickers", "price": 10000, "count": 8, "category": "snack"},
            "lays": {"name_uz": "Lays chipslari", "name_ru": "Чипсы Lays", "name_en": "Lays Chips", "price": 9000, "count": 5, "category": "snack"}
        }
        save_products(default_products)
        return default_products
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_products(products_data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products_data, f, ensure_ascii=False, indent=4)

PRODUCTS = load_products()

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def set_bot_commands():
    commands = [
        types.BotCommand("start", "Botni qayta ishga tushirish / Restart bot 🔄")
    ]
    bot.set_my_commands(commands)

def get_main_keyboard(lang):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    if lang == 'ru':
        btn_products = types.KeyboardButton("☕ Товары и Цены")
        btn_lang = types.KeyboardButton("🌐 Сменить язык")
        btn_suggest = types.KeyboardButton("💡 Есть предложение")
        btn_complaint = types.KeyboardButton("⚠️ Есть жалоба")
    elif lang == 'en':
        btn_products = types.KeyboardButton("☕ Products & Prices")
        btn_lang = types.KeyboardButton("🌐 Change Language")
        btn_suggest = types.KeyboardButton("💡 Suggestion")
        btn_complaint = types.KeyboardButton("⚠️ Complaint")
    else:
        btn_products = types.KeyboardButton("☕ Mahsulotlar va Narxlar")
        btn_lang = types.KeyboardButton("🌐 Tilni tanlash")
        btn_suggest = types.KeyboardButton("💡 Taklifim bor")
        btn_complaint = types.KeyboardButton("⚠️ Shikoyatim bor")
        
    keyboard.add(btn_products, btn_lang, btn_suggest, btn_complaint)
    return keyboard

# 1. /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_uz = types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="setlang_uz")
    btn_ru = types.InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang_ru")
    btn_en = types.InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en")
    markup.add(btn_uz, btn_ru, btn_en)
    
    user_name = html.escape(message.from_user.first_name or "")
    welcome_text = (
        f"Assalomu alaykum, hurmatli {user_name}! 😊\n"
        f"Bizning vending xizmatimiz botiga xush kelibsiz.\n\n"
        f"Iltimos, muloqot tilini tanlang:\n"
        f"Пожалуйста, выберите язык:\n"
        f"Please select your language:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('setlang_'))
def handle_language_choice(call):
    lang = call.data.split('_')[1]
    user_lang[call.message.chat.id] = lang
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    if lang == 'ru':
        text = "Выбран русский язык! 🇷🇺\n\nРады помочь вам! Вы можете использовать меню ниже:"
    elif lang == 'en':
        text = "English language selected! 🇬🇧\n\nWe are happy to serve you! Please use the menu below:"
    else:
        text = "O'zbek tili tanlandi! 🇺🇿\n\nSizga xizmat ko'rsatishdan mamnunmiz! Quyidagi menyudan kerakli bo'limni tanlashingiz mumkin:"
        
    bot.send_message(call.message.chat.id, text, reply_markup=get_main_keyboard(lang))

# 2. MIJOZ MENYUSI
@bot.message_handler(func=lambda message: message.text in ["☕ Mahsulotlar va Narxlar", "☕ Товары и Цены", "☕ Products & Prices"])
def show_categories(message):
    lang = user_lang.get(message.chat.id, 'uz')
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if lang == 'ru':
        markup.add(
            types.InlineKeyboardButton("🍫 Снеки и сладости", callback_data="cat_snack"),
            types.InlineKeyboardButton("🥤 Напитки", callback_data="maincat_drinks"),
            types.InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
        )
        text = "📂 Выберите категорию товаров:"
    elif lang == 'en':
        markup.add(
            types.InlineKeyboardButton("🍫 Snacks & Sweets", callback_data="cat_snack"),
            types.InlineKeyboardButton("🥤 Drinks", callback_data="maincat_drinks"),
            types.InlineKeyboardButton("🔙 Main Menu", callback_data="back_to_main")
        )
        text = "📂 Select product category:"
    else:
        markup.add(
            types.InlineKeyboardButton("🍫 Snek va shirinliklar", callback_data="cat_snack"),
            types.InlineKeyboardButton("🥤 Ichimliklar", callback_data="maincat_drinks"),
            types.InlineKeyboardButton("🔙 Asosiy menyu", callback_data="back_to_main")
        )
        text = "📂 Mahsulotlar bo'limini tanlang:"
        
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "maincat_drinks")
def show_drink_subcategories(call):
    lang = user_lang.get(call.message.chat.id, 'uz')
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if lang == 'ru':
        markup.add(
            types.InlineKeyboardButton("⚡ Энергетические напитки", callback_data="cat_energy"),
            types.InlineKeyboardButton("🥤 Газированные напитки", callback_data="cat_carbonated"),
            types.InlineKeyboardButton("💧 Негазированные напитки", callback_data="cat_still"),
            types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_cats")
        )
        text = "🥤 Выберите тип напитка:"
    elif lang == 'en':
        markup.add(
            types.InlineKeyboardButton("⚡ Energy Drinks", callback_data="cat_energy"),
            types.InlineKeyboardButton("🥤 Carbonated Drinks", callback_data="cat_carbonated"),
            types.InlineKeyboardButton("💧 Still Drinks", callback_data="cat_still"),
            types.InlineKeyboardButton("🔙 Back", callback_data="back_to_cats")
        )
        text = "🥤 Select drink type:"
    else:
        markup.add(
            types.InlineKeyboardButton("⚡ Energetik ichimliklar", callback_data="cat_energy"),
            types.InlineKeyboardButton("🥤 Gazlangan ichimliklar", callback_data="cat_carbonated"),
            types.InlineKeyboardButton("💧 Gazlanmagan ichimliklar", callback_data="cat_still"),
            types.InlineKeyboardButton("🔙 Ortga", callback_data="back_to_cats")
        )
        text = "🥤 Ichimliklar turini tanlang:"
        
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def show_products_in_category(call):
    cat = call.data.split('_')[1]
    lang = user_lang.get(call.message.chat.id, 'uz')
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    count_items = 0
    for key, item in PRODUCTS.items():
        if item["category"] == cat:
            count_items += 1
            if lang == 'ru':
                name = item.get("name_ru", item["name_uz"])
            elif lang == 'en':
                name = item.get("name_en", item["name_uz"])
            else:
                name = item["name_uz"]
            markup.add(types.InlineKeyboardButton(f"🔹 {name}", callback_data=f"prod_{key}"))
            
    back_target = "maincat_drinks" if cat in ["energy", "carbonated", "still"] else "back_to_cats"
    btn_text = "🔙 Ortga" if lang == 'uz' else ("🔙 Назад" if lang == 'ru' else "🔙 Back")
    markup.add(types.InlineKeyboardButton(btn_text, callback_data=back_target))

    if count_items == 0:
        if lang == 'ru':
            empty_text = "В этой категории пока нет товаров."
        elif lang == 'en':
            empty_text = "There are currently no products in this category."
        else:
            empty_text = "Hozircha bu bo'limda mahsulot mavjud emas."
        bot.edit_message_text(empty_text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        return
            
    text = "Выберите товар:" if lang == 'ru' else ("Select product:" if lang == 'en' else "Mahsulotni tanlang:")
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('prod_'))
def show_product_details(call):
    prod_key = call.data.replace('prod_', '', 1)
    lang = user_lang.get(call.message.chat.id, 'uz')
    
    if prod_key not in PRODUCTS:
        alert_msg = "Mahsulot topilmadi!" if lang == 'uz' else ("Товар не найден!" if lang == 'ru' else "Product not found!")
        bot.answer_callback_query(call.id, alert_msg, show_alert=True)
        show_categories(call.message)
        return

    item = PRODUCTS[prod_key]
    if lang == 'ru':
        name = html.escape(item.get("name_ru", item["name_uz"]))
        text = f"📦 <b>Товар:</b> {name}\n💰 <b>Цена:</b> {item['price']:,} сум\n📊 <b>В наличии:</b> {item['count']} шт."
        btn_out = types.InlineKeyboardButton("🚨 Сообщить: Товар закончился", callback_data=f"outofstock_{prod_key}")
        btn_back = types.InlineKeyboardButton("🔙 Назад к списку", callback_data=f"cat_{item['category']}")
    elif lang == 'en':
        name = html.escape(item.get("name_en", item["name_uz"]))
        text = f"📦 <b>Product:</b> {name}\n💰 <b>Price:</b> {item['price']:,} UZS\n📊 <b>In stock:</b> {item['count']} pcs"
        btn_out = types.InlineKeyboardButton("🚨 Report: Out of stock", callback_data=f"outofstock_{prod_key}")
        btn_back = types.InlineKeyboardButton("🔙 Back to list", callback_data=f"cat_{item['category']}")
    else:
        name = html.escape(item["name_uz"])
        text = f"📦 <b>Mahsulot:</b> {name}\n💰 <b>Narxi:</b> {item['price']:,} so'm\n📊 <b>Qurilmada mavjud:</b> {item['count']} ta"
        btn_out = types.InlineKeyboardButton("🚨 Mahsulot tugadi (Xabar berish)", callback_data=f"outofstock_{prod_key}")
        btn_back = types.InlineKeyboardButton("🔙 Ortga", callback_data=f"cat_{item['category']}")
        
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(btn_out, btn_back)
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_cats")
def back_to_categories(call):
    show_categories(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_menu(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

# MAHSULOT TUGAGANI HAQIDA RASMLI XABAR YUBORISH
@bot.callback_query_handler(func=lambda call: call.data.startswith('outofstock_'))
def start_report_out_of_stock(call):
    prod_key = call.data.replace('outofstock_', '', 1)
    if prod_key not in PRODUCTS:
        return
        
    lang = user_lang.get(call.message.chat.id, 'uz')
    bot.answer_callback_query(call.id)
    
    user_states[call.message.chat.id] = prod_key
    
    if lang == 'ru':
        msg_text = "📸 Пожалуйста, отправьте фотографию автомата или полки, подтверждающую, что товар закончился:"
    elif lang == 'en':
        msg_text = "📸 Please send a photo of the vending machine shelf confirming the product is out of stock:"
    else:
        msg_text = "📸 Iltimos, mahsulot tugaganini tasdiqlash uchun apparatdagi o'sha joyning <b>rasmini yuboring</b>:"
        
    msg = bot.send_message(call.message.chat.id, msg_text, parse_mode="HTML")
    bot.register_next_step_handler(msg, process_out_of_stock_photo)

def process_out_of_stock_photo(message):
    lang = user_lang.get(message.chat.id, 'uz')
    prod_key = user_states.get(message.chat.id)
    
    if message.content_type != 'photo':
        if lang == 'ru':
            error_text = "❌ Это не фотография. Пожалуйста, отправьте фото товара/автомата:"
        elif lang == 'en':
            error_text = "❌ This is not a photo. Please send a photo of the vending machine:"
        else:
            error_text = "❌ Rasm yuborilmadi. Iltimos, apparatdagi mahsulot joyining rasmini tushirib yuboring:"
        msg = bot.send_message(message.chat.id, error_text)
        bot.register_next_step_handler(msg, process_out_of_stock_photo)
        return

    item = PRODUCTS.get(prod_key, {})
    prod_name = html.escape(item.get('name_uz', 'Noma\'lum mahsulot'))
    user = message.from_user
    username = html.escape(user.username) if user.username else 'yoq'
    first_name = html.escape(user.first_name or "")
    
    admin_alert = (
        f"🚨 <b>DIQQAT! MAHSULOT TUGAGANI HAQIDA MURAJAAT!</b>\n\n"
        f"📌 <b>Mahsulot:</b> {prod_name}\n"
        f"👤 <b>Mijoz:</b> @{username} ({first_name})\n"
        f"🆔 <b>Mijoz ID:</b> <code>{message.chat.id}</code>\n\n"
        f"<i>Mahsulot sonini 0 ga tushirishni tasdiqlaysizmi?</i>"
    )
    
    # Admin uchun Tasdiqlash va Rad etish tugmalari
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_confirm = types.InlineKeyboardButton("✅ Tasdiqlash (Soni -> 0)", callback_data=f"confirmzero_{prod_key}_{message.chat.id}")
    btn_reject = types.InlineKeyboardButton("❌ Rad etish", callback_data=f"rejectzero_{prod_key}_{message.chat.id}")
    markup.add(btn_confirm, btn_reject)

    photo_file_id = message.photo[-1].file_id
    bot.send_photo(ADMIN_ID, photo_file_id, caption=admin_alert, parse_mode="HTML", reply_markup=markup)
    
    if lang == 'ru':
        thanks_text = (
            "🌟 <b>Огромное спасибо!</b>\n\n"
            "Ваше сообщение и фотография отправлены администратору. "
            "После проверки информации автомат будет обновлен! 🤝✨"
        )
    elif lang == 'en':
        thanks_text = (
            "🌟 <b>Thank you very much!</b>\n\n"
            "Your report and photo have been sent to the admin. "
            "The machine info will be updated after verification! 🤝✨"
        )
    else:
        thanks_text = (
            "🌟 <b>Katta rahmat!</b>\n\n"
            "Xabaringiz va rasmingiz adminga yetkazildi. "
            "Admin tomonidan tekshirilgach, apparat zudlik bilan yangilanadi! 🤝✨"
        )
        
    bot.send_message(message.chat.id, thanks_text, parse_mode="HTML", reply_markup=get_main_keyboard(lang))

# ADMIN UCHUN TASDIQLASH VA RAD ETISH CALLBACK HANDLERLARI
@bot.callback_query_handler(func=lambda call: call.data.startswith(('confirmzero_', 'rejectzero_')))
def handle_zero_confirmation(call):
    if call.message.chat.id != ADMIN_ID: return
    
    action, prod_key, user_id = call.data.split('_')
    item = PRODUCTS.get(prod_key)
    prod_name = html.escape(item['name_uz']) if item else "Mahsulot"
    user_lang_code = user_lang.get(int(user_id), 'uz')

    if action == "confirmzero":
        if prod_key in PRODUCTS:
            PRODUCTS[prod_key]['count'] = 0
            save_products(PRODUCTS)
            
        bot.edit_message_caption(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            caption=call.message.caption + f"\n\n<b>✅ ADMIN TAROFIDAN TASDIQLANDI!</b> Soni 0 ga tushirildi.", 
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id, "✅ Mahsulot soni 0 deb saqlandi!", show_alert=True)
        
        # Mijozga bildirishnoma yuborish
        msg_to_user = f"✅ <b>{prod_name}</b> bo'yicha yuborgan xabaringiz admin tomonidan tasdiqlandi. Tez orada apparat to'ldiriladi! Rahmat!"
        try: bot.send_message(user_id, msg_to_user, parse_mode="HTML")
        except: pass

    elif action == "rejectzero":
        bot.edit_message_caption(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            caption=call.message.caption + f"\n\n<b>❌ RAD ETILDI.</b> Mahsulot soni o'zgartirilmadi.", 
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id, "❌ So'rov rad etildi.", show_alert=True)
        
        # Mijozga bildirishnoma yuborish
        msg_to_user = f"ℹ️ <b>{prod_name}</b> bo'yicha yuborgan murojaatingiz ko'rib chiqildi. E'tiboringiz uchun rahmat!"
        try: bot.send_message(user_id, msg_to_user, parse_mode="HTML")
        except: pass

@bot.message_handler(func=lambda message: message.text in ["🌐 Tilni tanlash", "🌐 Сменить язык", "🌐 Change Language"])
def change_language_menu(message):
    send_welcome(message)

# TAKLIF YUBORISH
@bot.message_handler(func=lambda message: message.text in ["💡 Taklifim bor", "💡 Есть предложение", "💡 Suggestion"])
def handle_suggestion_button(message):
    lang = user_lang.get(message.chat.id, 'uz')
    if lang == 'ru':
        msg_text = "💡 Напишите ваше предложение (текстом или отправьте фото):"
    elif lang == 'en':
        msg_text = "💡 Please write your suggestion (text or send a photo):"
    else:
        msg_text = "💡 Biz xizmatimizni yanada yaxshilashga intilamiz. Taklifingizni matn yoki rasm ko'rinishida yuboring:"
    msg = bot.send_message(message.chat.id, msg_text)
    bot.register_next_step_handler(msg, process_suggestion)

def process_suggestion(message):
    lang = user_lang.get(message.chat.id, 'uz')
    user = message.from_user
    username = html.escape(user.username) if user.username else 'yoq'
    first_name = html.escape(user.first_name or "")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_{message.chat.id}"))
    
    user_info = f"💡 <b>YANGI TAKLIF!</b>\n\nKimdan: @{username} ({first_name})\nID: <code>{message.chat.id}</code>"
    
    if message.content_type == 'text':
        text_content = html.escape(message.text)
        bot.send_message(ADMIN_ID, f"{user_info}\n\nTaklif: {text_content}", parse_mode="HTML", reply_markup=markup)
    elif message.content_type == 'photo':
        caption_text = html.escape(message.caption or '')
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"{user_info}\n\nIzoh: {caption_text}", parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Iltimos, faqat matn yoki rasm yuboring.", reply_markup=get_main_keyboard(lang))
        return

    if lang == 'ru':
        thanks = "🌟 <b>Большое спасибо!</b>\nВаше предложение успешно отправлено администратору. Оно обязательно будет учтено! 💡😊"
    elif lang == 'en':
        thanks = "🌟 <b>Thank you very much!</b>\nYour suggestion has been sent to the admin. We will definitely consider it! 💡😊"
    else:
        thanks = "🌟 <b>Katta rahmat!</b>\nQimmatli taklifingiz adminga yetkazildi. Taklifingiz albatta inobatga olinadi va xizmatimizni yanada rivojlantirishga yordam beradi! 💡😊"
        
    bot.send_message(message.chat.id, thanks, parse_mode="HTML", reply_markup=get_main_keyboard(lang))

# SHIKOYAT YUBORISH
@bot.message_handler(func=lambda message: message.text in ["⚠️ Shikoyatim bor", "⚠️ Есть жалоба", "⚠️ Complaint"])
def handle_complaint_button(message):
    lang = user_lang.get(message.chat.id, 'uz')
    if lang == 'ru':
        msg_text = "⚠️ Напишите подробности вашей жалобы (текстом или отправьте фото):"
    elif lang == 'en':
        msg_text = "⚠️ Please write the details of your complaint (text or send a photo):"
    else:
        msg_text = "⚠️ Yuzaga kelgan noqulaylik uchun uzr so'raymiz! Shikoyatingiz tafsilotlarini yozib yoki rasm bilan yuboring:"
    msg = bot.send_message(message.chat.id, msg_text)
    bot.register_next_step_handler(msg, process_complaint)

def process_complaint(message):
    lang = user_lang.get(message.chat.id, 'uz')
    user = message.from_user
    username = html.escape(user.username) if user.username else 'yoq'
    first_name = html.escape(user.first_name or "")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_{message.chat.id}"))
    
    user_info = f"⚠️ <b>YANGI SHIKOYAT!</b>\n\nKimdan: @{username} ({first_name})\nID: <code>{message.chat.id}</code>"
    
    if message.content_type == 'text':
        text_content = html.escape(message.text)
        bot.send_message(ADMIN_ID, f"{user_info}\n\nShikoyat: {text_content}", parse_mode="HTML", reply_markup=markup)
    elif message.content_type == 'photo':
        caption_text = html.escape(message.caption or '')
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"{user_info}\n\nIzoh: {caption_text}", parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Iltimos, faqat matn yoki rasm yuboring.", reply_markup=get_main_keyboard(lang))
        return

    if lang == 'ru':
        thanks = "Приносим свои извинения за неудобства! 🙏 Ваше обращение отправлено администратору. Мы обязательно изучим проблему и устраним ее в кратчайшие сроки!"
    elif lang == 'en':
        thanks = "We sincerely apologize for the inconvenience! 🙏 Your complaint has been sent to the admin. We will investigate and resolve the issue as soon as possible!"
    else:
        thanks = "Yuzaga kelgan noqulaylik va xatolik uchun chin ko'ngildan uzr so'raymiz! 🙏 Shikoyatingiz adminga yetkazildi. Muammo albatta o'rganib chiqiladi, xatoni darhol to'g'rilaymiz va vaziyatni nazoratga olamiz."
        
    bot.send_message(message.chat.id, thanks, parse_mode="HTML", reply_markup=get_main_keyboard(lang))

# 3. ADMIN PANEL (Faqat ADMIN_ID uchun)
@bot.message_handler(commands=['admin', 'setprice'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        return
    render_admin_main(message)

def render_admin_main(call_or_msg):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📝 Narx, sonini o'zgartirish va O'CHIRISH", callback_data="admin_select_cat"),
        types.InlineKeyboardButton("➕ Yangi mahsulot qo'shish", callback_data="admin_add_new")
    )
    if hasattr(call_or_msg, 'message'):
        bot.edit_message_text("🛠 <b>ADMIN PANEL</b>\n\nKerakli bo'limni tanlang:", call_or_msg.message.chat.id, call_or_msg.message.message_id, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, "🛠 <b>ADMIN PANEL</b>\n\nKerakli bo'limni tanlang:", parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_main")
def callback_admin_main(call):
    if call.message.chat.id != ADMIN_ID: return
    render_admin_main(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_select_cat")
def admin_select_category_to_edit(call):
    if call.message.chat.id != ADMIN_ID: return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🍫 Snek va shirinliklar", callback_data="admeditcat_snack"),
        types.InlineKeyboardButton("⚡ Energetik ichimliklar", callback_data="admeditcat_energy"),
        types.InlineKeyboardButton("🥤 Gazlangan ichimliklar", callback_data="admeditcat_carbonated"),
        types.InlineKeyboardButton("💧 Gazlanmagan ichimliklar", callback_data="admeditcat_still"),
        types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main")
    )
    bot.edit_message_text("📂 Qaysi bo'limdagi mahsulotlarni tahrirlamoqchisiz?", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('admeditcat_'))
def admin_show_products_by_cat(call):
    if call.message.chat.id != ADMIN_ID: return
    cat = call.data.split('_')[1]
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    count = 0
    for key, item in PRODUCTS.items():
        if item['category'] == cat:
            count += 1
            markup.add(types.InlineKeyboardButton(f"⚙️ {item['name_uz']} ({item['price']} so'm | {item['count']} ta)", callback_data=f"adm_edit_{key}"))
            
    markup.add(types.InlineKeyboardButton("🔙 Ortga", callback_data="admin_select_cat"))
    markup.add(types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main"))

    if count == 0:
        bot.edit_message_text("Ushbu bo'limda hozircha mahsulot yo'q.", call.message.chat.id, call.message.message_id, reply_markup=markup)
        return
        
    bot.edit_message_text(f"📌 <b>{SUB_CATEGORIES.get(cat, 'Bo\'lim')}</b> mahsulotlari:\nTahrirlash yoki o'chirish uchun birini tanlang:", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_'))
def admin_choose_option(call):
    if call.message.chat.id != ADMIN_ID: return
    prod_key = call.data.replace('adm_edit_', '', 1)
    
    if prod_key not in PRODUCTS:
        render_admin_main(call)
        return

    item = PRODUCTS[prod_key]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("💰 Narxni o'zgartirish", callback_data=f"changep_{prod_key}"),
        types.InlineKeyboardButton("📊 Soni (Qoldiq)ni o'zgartirish", callback_data=f"changec_{prod_key}"),
        types.InlineKeyboardButton("🗑 Mahsulotni BUTUNLAY O'CHIRISH", callback_data=f"deletep_{prod_key}"),
        types.InlineKeyboardButton("🔙 Ortga (Ro'yxatga)", callback_data=f"admeditcat_{item['category']}"),
        types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main")
    )
    name = html.escape(item['name_uz'])
    bot.edit_message_text(f"📌 <b>{name}</b> bo'yicha amalni tanlang:", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('deletep_'))
def admin_delete_product(call):
    if call.message.chat.id != ADMIN_ID: return
    prod_key = call.data.replace('deletep_', '', 1)
    
    if prod_key in PRODUCTS:
        deleted_name = html.escape(PRODUCTS[prod_key]['name_uz'])
        cat = PRODUCTS[prod_key]['category']
        
        del PRODUCTS[prod_key]
        save_products(PRODUCTS)
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔙 Ro'yxatga qaytish", callback_data=f"admeditcat_{cat}"))
        markup.add(types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main"))
        bot.edit_message_text(f"🗑 <b>{deleted_name}</b> butunlay o'chirib tashlandi!", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
    else:
        render_admin_main(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('changep_', 'changec_')))
def admin_input_prompt(call):
    if call.message.chat.id != ADMIN_ID: return
    
    if call.data.startswith('changep_'):
        action = 'changep'
        prod_key = call.data.replace('changep_', '', 1)
    else:
        action = 'changec'
        prod_key = call.data.replace('changec_', '', 1)
    
    if prod_key not in PRODUCTS:
        render_admin_main(call)
        return

    name = html.escape(PRODUCTS[prod_key]['name_uz'])
    if action == 'changep':
        msg = bot.send_message(ADMIN_ID, f"✍️ <code>{name}</code> uchun yangi <b>narxni</b> kiriting:\n\n*(Bekor qilish uchun <b>bekor</b> deb yozing)*", parse_mode="HTML")
        bot.register_next_step_handler(msg, update_price, prod_key)
    elif action == 'changec':
        msg = bot.send_message(ADMIN_ID, f"✍️ <code>{name}</code> uchun yangi <b>soni (dona)</b>ni kiriting:\n\n*(Bekor qilish uchun <b>bekor</b> deb yozing)*", parse_mode="HTML")
        bot.register_next_step_handler(msg, update_count, prod_key)

def update_price(message, prod_key):
    if message.text and message.text.lower() == 'bekor':
        bot.send_message(ADMIN_ID, "Amal bekor qilindi.")
        render_admin_main(message)
        return
    if not message.text or not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Faqat raqam kiriting.")
        render_admin_main(message)
        return
    if prod_key in PRODUCTS:
        PRODUCTS[prod_key]['price'] = int(message.text)
        save_products(PRODUCTS)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main"))
        name = html.escape(PRODUCTS[prod_key]['name_uz'])
        bot.send_message(ADMIN_ID, f"✅ <code>{name}</code> narxi <b>{int(message.text):,} so'm</b>ga o'zgartirildi!", parse_mode="HTML", reply_markup=markup)

def update_count(message, prod_key):
    if message.text and message.text.lower() == 'bekor':
        bot.send_message(ADMIN_ID, "Amal bekor qilindi.")
        render_admin_main(message)
        return
    if not message.text or not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Faqat raqam kiriting.")
        render_admin_main(message)
        return
    if prod_key in PRODUCTS:
        PRODUCTS[prod_key]['count'] = int(message.text)
        save_products(PRODUCTS)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main"))
        name = html.escape(PRODUCTS[prod_key]['name_uz'])
        bot.send_message(ADMIN_ID, f"✅ <code>{name}</code> soni <b>{int(message.text)} ta</b> deb yangilandi!", parse_mode="HTML", reply_markup=markup)

# ADMIN - YANGI MAHSULOT QO'SHISH
@bot.callback_query_handler(func=lambda call: call.data == "admin_add_new")
def admin_add_new_start(call):
    if call.message.chat.id != ADMIN_ID: return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🍫 Sneklar", callback_data="addcat_snack"),
        types.InlineKeyboardButton("⚡ Energetik ichimliklar", callback_data="addcat_energy"),
        types.InlineKeyboardButton("🥤 Gazlangan ichimliklar", callback_data="addcat_carbonated"),
        types.InlineKeyboardButton("💧 Gazlanmagan ichimliklar", callback_data="addcat_still"),
        types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main")
    )
    bot.edit_message_text("➕ Yangi mahsulot qaysi toifaga kiradi?", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('addcat_'))
def admin_add_get_category(call):
    if call.message.chat.id != ADMIN_ID: return
    cat = call.data.split('_')[1]
    admin_temp_data[ADMIN_ID] = {"category": cat}
    
    msg = bot.send_message(ADMIN_ID, f"✍️ <b>{SUB_CATEGORIES.get(cat)}</b> uchun mahsulot nomini kiriting:\n\n*(Bekor qilish uchun <b>bekor</b> deb yozing)*", parse_mode="HTML")
    bot.register_next_step_handler(msg, admin_add_get_name)

def admin_add_get_name(message):
    if message.text and message.text.lower() == 'bekor':
        bot.send_message(ADMIN_ID, "Bekor qilindi.")
        render_admin_main(message)
        return
    admin_temp_data[ADMIN_ID]["name"] = message.text
    name = html.escape(message.text)
    msg = bot.send_message(ADMIN_ID, f"✍️ <code>{name}</code> narxini kiriting (masalan: 9000):\n\n*(Bekor qilish uchun <b>bekor</b> deb yozing)*", parse_mode="HTML")
    bot.register_next_step_handler(msg, admin_add_get_price)

def admin_add_get_price(message):
    if message.text and message.text.lower() == 'bekor':
        bot.send_message(ADMIN_ID, "Bekor qilindi.")
        render_admin_main(message)
        return
    if not message.text or not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Faqat raqam kiriting.")
        render_admin_main(message)
        return
    admin_temp_data[ADMIN_ID]["price"] = int(message.text)
    msg = bot.send_message(ADMIN_ID, "✍️ Apparatga nechta dona qo'ydingiz?\n\n*(Bekor qilish uchun <b>bekor</b> deb yozing)*", parse_mode="HTML")
    bot.register_next_step_handler(msg, admin_add_finish)

def admin_add_finish(message):
    if message.text and message.text.lower() == 'bekor':
        bot.send_message(ADMIN_ID, "Bekor qilindi.")
        render_admin_main(message)
        return
    if not message.text or not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Faqat raqam kiriting.")
        render_admin_main(message)
        return
    
    count = int(message.text)
    data = admin_temp_data[ADMIN_ID]
    new_key = f"item_{int(time.time())}"
    
    PRODUCTS[new_key] = {
        "name_uz": data["name"],
        "name_ru": data["name"],
        "name_en": data["name"],
        "price": data["price"],
        "count": count,
        "category": data["category"]
    }
    
    save_products(PRODUCTS)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main"))
    
    name = html.escape(data['name'])
    bot.send_message(
        ADMIN_ID, 
        f"🎉 <b>Yangi mahsulot qo'shildi!</b>\n\n📌 Nomi: {name}\n📂 Bo'lim: {SUB_CATEGORIES.get(data['category'])}\n💰 Narxi: {data['price']:,} so'm\n📊 Soni: {count} ta",
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def ask_admin_reply(call):
    target_user_id = call.data.split('_')[1]
    msg = bot.send_message(ADMIN_ID, f"✍️ Javobingizni yozing (ID: <code>{target_user_id}</code>):", parse_mode="HTML")
    bot.register_next_step_handler(msg, send_reply_to_user, target_user_id)

def send_reply_to_user(message, target_user_id):
    try:
        reply_text = html.escape(message.text)
        bot.send_message(target_user_id, f"💬 <b>Ma'muriyatdan javob / Response from support:</b>\n\n{reply_text}", parse_mode="HTML")
        bot.send_message(ADMIN_ID, "✅ Javob foydalanuvchiga yetkazildi!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Xatolik yuz berdi: {e}")

# AVTO-RECONNECT 24/7
def run_bot():
    try:
        set_bot_commands()
    except Exception as e:
        print(f"Buyruqlarni o'rnatishda xatolik: {e}")
        
    bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
