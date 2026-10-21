import os
import time
import json
import threading
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

# MAHSULOTLARNI FAYLGA SAQLASH VA O me'yorida O'QISH TIZIMI
DATA_FILE = "products.json"

def load_products():
    if not os.path.exists(DATA_FILE):
        default_products = {
            "redbull": {"name_uz": "Red Bull 0.25L", "name_ru": "Red Bull 0.25Л", "price": 18000, "count": 10, "category": "energy"},
            "flash": {"name_uz": "Flash Up 0.45L", "name_ru": "Flash Up 0.45Л", "price": 8000, "count": 15, "category": "energy"},
            "pepsi": {"name_uz": "Pepsi 0.5L", "name_ru": "Пепси 0.5Л", "price": 9000, "count": 15, "category": "carbonated"},
            "snickers": {"name_uz": "Snickers", "name_ru": "Snickers", "price": 10000, "count": 8, "category": "snack"},
            "lays": {"name_uz": "Lays chipslari", "name_ru": "Чипсы Lays", "price": 9000, "count": 5, "category": "snack"}
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

# 1. /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_uz = types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="setlang_uz")
    btn_ru = types.InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang_ru")
    markup.add(btn_uz, btn_ru)
    
    user_name = message.from_user.first_name
    welcome_text = (
        f"Assalomu alaykum, {user_name}!\n"
        f"Bizning vending xizmatimiz botiga xush kelibsiz.\n\n"
        f"Iltimos, muloqot tilini tanlang:\n"
        f"Здравствуйте! Пожалуйста, выберите язык:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('setlang_'))
def handle_language_choice(call):
    lang = call.data.split('_')[1]
    user_lang[call.message.chat.id] = lang
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    text = "O'zbek tili tanlandi! 🇺🇿\nQuyidagi menyudan foydalanishingiz mumkin:" if lang == 'uz' else "Выбран русский язык! 🇷🇺\nВы можете использовать меню ниже:"
    bot.send_message(call.message.chat.id, text, reply_markup=get_main_keyboard(lang))

# 2. MIJOZ MENYUSI
@bot.message_handler(func=lambda message: message.text in ["☕ Mahsulotlar va Narxlar", "☕ Товары и Цены"])
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
            name = item["name_ru"] if lang == 'ru' else item["name_uz"]
            markup.add(types.InlineKeyboardButton(f"🔹 {name}", callback_data=f"prod_{key}"))
            
    back_target = "maincat_drinks" if cat in ["energy", "carbonated", "still"] else "back_to_cats"
    btn_back = types.InlineKeyboardButton("🔙 Ortga" if lang == 'uz' else "🔙 Назад", callback_data=back_target)
    markup.add(btn_back)

    if count_items == 0:
        empty_text = "Hozircha bu bo'limda mahsulot yo'q." if lang == 'uz' else "В этой категории пока нет товаров."
        bot.edit_message_text(empty_text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        return
            
    text = "Выберите товар:" if lang == 'ru' else "Mahsulotni tanlang:"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('prod_'))
def show_product_details(call):
    prod_key = call.data.split('_')[1]
    lang = user_lang.get(call.message.chat.id, 'uz')
    
    if prod_key not in PRODUCTS:
        bot.answer_callback_query(call.id, "Mahsulot o'chirilgan!", show_alert=True)
        show_categories(call.message)
        return

    item = PRODUCTS[prod_key]
    name = item["name_ru"] if lang == 'ru' else item["name_uz"]
    
    if lang == 'ru':
        text = f"📦 **Товар:** {name}\n💰 **Цена:** {item['price']:,} сум\n📊 **В наличии:** {item['count']} шт."
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
    show_categories(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main_menu(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('outofstock_'))
def report_out_of_stock(call):
    prod_key = call.data.split('_')[1]
    if prod_key not in PRODUCTS: return
    item = PRODUCTS[prod_key]
    user = call.from_user
    lang = user_lang.get(call.message.chat.id, 'uz')
    
    confirm_text = "Rahmat! Adminlarga xabar berildi." if lang == 'uz' else "Спасибо! Уведомление отправлено."
    bot.answer_callback_query(call.id, confirm_text, show_alert=True)
    
    admin_alert = f"⚠️ **DIQQAT! MAHSULOT TUGADI!**\n\nFoydalanuvchi @{user.username or 'yoq'} ({user.first_name}) ma'lum qildi:\n📌 **{item['name_uz']}**"
    bot.send_message(ADMIN_ID, admin_alert, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text in ["🌐 Tilni tanlash", "🌐 Сменить язык"])
def change_language_menu(message):
    send_welcome(message)

# TAKLIF VA SHIKOYATLAR
@bot.message_handler(func=lambda message: message.text in ["💡 Taklifim bor", "💡 Есть предложение"])
def handle_suggestion_button(message):
    lang = user_lang.get(message.chat.id, 'uz')
    msg = bot.send_message(message.chat.id, "Taklifingiz bo'lsa yozib yuboring:" if lang == 'uz' else "Напишите ваше предложение:")
    bot.register_next_step_handler(msg, process_suggestion)

def process_suggestion(message):
    lang = user_lang.get(message.chat.id, 'uz')
    user = message.from_user
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_{message.chat.id}"))
    
    user_info = f"💡 **YANGI TAKLIF!**\n\nKimdan: @{user.username or 'yoq'} ({user.first_name})\nID: {message.chat.id}"
    if message.content_type == 'text':
        bot.send_message(ADMIN_ID, f"{user_info}\n\nTaklif: {message.text}", reply_markup=markup)
    elif message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"{user_info}\n\nIzoh: {message.caption or ''}", reply_markup=markup)
        
    bot.send_message(message.chat.id, "Rahmat, taklifingiz uchun!" if lang == 'uz' else "Спасибо за предложение!", reply_markup=get_main_keyboard(lang))

@bot.message_handler(func=lambda message: message.text in ["⚠️ Shikoyatim bor", "⚠️ Есть жалоба"])
def handle_complaint_button(message):
    lang = user_lang.get(message.chat.id, 'uz')
    msg = bot.send_message(message.chat.id, "Shikoyatingizni yozib yuboring:" if lang == 'uz' else "Напишите подробности вашей жалобы:")
    bot.register_next_step_handler(msg, process_complaint)

def process_complaint(message):
    lang = user_lang.get(message.chat.id, 'uz')
    user = message.from_user
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_{message.chat.id}"))
    
    user_info = f"⚠️ **YANGI SHIKOYAT!**\n\nKimdan: @{user.username or 'yoq'} ({user.first_name})\nID: {message.chat.id}"
    if message.content_type == 'text':
        bot.send_message(ADMIN_ID, f"{user_info}\n\nShikoyat: {message.text}", reply_markup=markup)
    elif message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"{user_info}\n\nIzoh: {message.caption or ''}", reply_markup=markup)
        
    bot.send_message(message.chat.id, "Rahmat, e'tirozingiz uchun!" if lang == 'uz' else "Спасибо за обращение!", reply_markup=get_main_keyboard(lang))

# 3. ADMIN PANEL (/admin)
@bot.message_handler(commands=['admin', 'setprice'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID: return
    render_admin_main(message)

def render_admin_main(call_or_msg):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📝 Narx, sonini o'zgartirish va O'CHIRISH", callback_data="admin_select_cat"),
        types.InlineKeyboardButton("➕ Yangi mahsulot qo'shish", callback_data="admin_add_new")
    )
    if hasattr(call_or_msg, 'message'):
        bot.edit_message_text("🛠 **ADMIN PANEL**\n\nKerakli bo'limni tanlang:", call_or_msg.message.chat.id, call_or_msg.message.message_id, reply_markup=markup)
    else:
        bot.send_message(ADMIN_ID, "🛠 **ADMIN PANEL**\n\nKerakli bo'limni tanlang:", reply_markup=markup)

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
        
    bot.edit_message_text(f"📌 **{SUB_CATEGORIES.get(cat, 'Bo\'lim')}** mahsulotlari:\nTahrirlash yoki o'chirish uchun birini tanlang:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_edit_'))
def admin_choose_option(call):
    if call.message.chat.id != ADMIN_ID: return
    prod_key = call.data.split('_')[2]
    
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
    bot.edit_message_text(f"📌 **{item['name_uz']}** bo'yicha amalni tanlang:", call.message.chat.id, call.message.message_id, reply_markup=markup)

# TO'LIQ O'CHIRISH VA FAYLGA SAQLASH
@bot.callback_query_handler(func=lambda call: call.data.startswith('deletep_'))
def admin_delete_product(call):
    if call.message.chat.id != ADMIN_ID: return
    prod_key = call.data.split('_')[1]
    
    if prod_key in PRODUCTS:
        deleted_name = PRODUCTS[prod_key]['name_uz']
        cat = PRODUCTS[prod_key]['category']
        
        # Bazadan ham, fayldan ham o'chirish
        del PRODUCTS[prod_key]
        save_products(PRODUCTS)
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔙 Ro'yxatga qaytish", callback_data=f"admeditcat_{cat}"))
        markup.add(types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main"))
        bot.edit_message_text(f"🗑 **{deleted_name}** butunlay o'chirib tashlandi!", call.message.chat.id, call.message.message_id, reply_markup=markup)
    else:
        render_admin_main(call)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('changep_', 'changec_')))
def admin_input_prompt(call):
    if call.message.chat.id != ADMIN_ID: return
    action, prod_key = call.data.split('_')
    
    if prod_key not in PRODUCTS:
        render_admin_main(call)
        return

    if action == 'changep':
        msg = bot.send_message(ADMIN_ID, f"✍️ `{PRODUCTS[prod_key]['name_uz']}` uchun yangi **narxni** kiriting:\n\n*(Bekor qilish uchun **bekor** deb yozing)*")
        bot.register_next_step_handler(msg, update_price, prod_key)
    elif action == 'changec':
        msg = bot.send_message(ADMIN_ID, f"✍️ `{PRODUCTS[prod_key]['name_uz']}` uchun yangi **soni (dona)**ni kiriting:\n\n*(Bekor qilish uchun **bekor** deb yozing)*")
        bot.register_next_step_handler(msg, update_count, prod_key)

def update_price(message, prod_key):
    if message.text.lower() == 'bekor':
        bot.send_message(ADMIN_ID, "Amal bekor qilindi.")
        render_admin_main(message)
        return
    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Faqat raqam kiriting.")
        render_admin_main(message)
        return
    if prod_key in PRODUCTS:
        PRODUCTS[prod_key]['price'] = int(message.text)
        save_products(PRODUCTS)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main"))
        bot.send_message(ADMIN_ID, f"✅ `{PRODUCTS[prod_key]['name_uz']}` narxi **{int(message.text):,} so'm**ga o'zgartirildi!", reply_markup=markup)

def update_count(message, prod_key):
    if message.text.lower() == 'bekor':
        bot.send_message(ADMIN_ID, "Amal bekor qilindi.")
        render_admin_main(message)
        return
    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Faqat raqam kiriting.")
        render_admin_main(message)
        return
    if prod_key in PRODUCTS:
        PRODUCTS[prod_key]['count'] = int(message.text)
        save_products(PRODUCTS)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main"))
        bot.send_message(ADMIN_ID, f"✅ `{PRODUCTS[prod_key]['name_uz']}` soni **{int(message.text)} ta** deb yangilandi!", reply_markup=markup)

# ADMIN - YANGI MAHSULOT QO'SHISH VA FAYLGA SAQLASH
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
    
    msg = bot.send_message(ADMIN_ID, f"✍️ **{SUB_CATEGORIES.get(cat)}** uchun mahsulot nomini kiriting:\n\n*(Bekor qilish uchun **bekor** deb yozing)*")
    bot.register_next_step_handler(msg, admin_add_get_name)

def admin_add_get_name(message):
    if message.text.lower() == 'bekor':
        bot.send_message(ADMIN_ID, "Bekor qilindi.")
        render_admin_main(message)
        return
    admin_temp_data[ADMIN_ID]["name"] = message.text
    msg = bot.send_message(ADMIN_ID, f"✍️ `{message.text}` narxini kiriting (masalan: 9000):\n\n*(Bekor qilish uchun **bekor** deb yozing)*")
    bot.register_next_step_handler(msg, admin_add_get_price)

def admin_add_get_price(message):
    if message.text.lower() == 'bekor':
        bot.send_message(ADMIN_ID, "Bekor qilindi.")
        render_admin_main(message)
        return
    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Faqat raqam kiriting.")
        render_admin_main(message)
        return
    admin_temp_data[ADMIN_ID]["price"] = int(message.text)
    msg = bot.send_message(ADMIN_ID, "✍️ Apparatga nechta dona qo'ydingiz?\n\n*(Bekor qilish uchun **bekor** deb yozing)*")
    bot.register_next_step_handler(msg, admin_add_finish)

def admin_add_finish(message):
    if message.text.lower() == 'bekor':
        bot.send_message(ADMIN_ID, "Bekor qilindi.")
        render_admin_main(message)
        return
    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Faqat raqam kiriting.")
        render_admin_main(message)
        return
    
    count = int(message.text)
    data = admin_temp_data[ADMIN_ID]
    new_key = f"prod_{int(time.time())}"
    
    PRODUCTS[new_key] = {
        "name_uz": data["name"],
        "name_ru": data["name"],
        "price": data["price"],
        "count": count,
        "category": data["category"]
    }
    
    save_products(PRODUCTS)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🏠 Admin menyusi", callback_data="admin_main"))
    
    bot.send_message(
        ADMIN_ID, 
        f"🎉 **Yangi mahsulot qo'shildi!**\n\n📌 Nomi: {data['name']}\n📂 Bo'lim: {SUB_CATEGORIES.get(data['category'])}\n💰 Narxi: {data['price']:,} so'm\n📊 Soni: {count} ta",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def ask_admin_reply(call):
    target_user_id = call.data.split('_')[1]
    msg = bot.send_message(ADMIN_ID, f"✍️ Javobingizni yozing (ID: {target_user_id}):")
    bot.register_next_step_handler(msg, send_reply_to_user, target_user_id)

def send_reply_to_user(message, target_user_id):
    try:
        bot.send_message(target_user_id, f"💬 Ma'muriyatdan javob:\n\n{message.text}")
        bot.send_message(ADMIN_ID, "✅ Javob yetkazildi!")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Xatolik: {e}")

# AVTO-RECONNECT 24/7
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
