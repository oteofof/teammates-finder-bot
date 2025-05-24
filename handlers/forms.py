from telebot import types
from datetime import datetime
from database import save_profile_to_db
from utils.formatters import format_profile
from config import DOTA_ROLES, VALORANT_RANKS, VALORANT_SUBRANKS

def ask_game(bot, message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_cs = types.KeyboardButton("CS2")
    btn_dota = types.KeyboardButton("Dota 2")
    btn_valorant = types.KeyboardButton("Valorant")
    markup.add(btn_cs, btn_dota, btn_valorant)
    
    msg = bot.send_message(message.chat.id, "🎮 Выбери игру:", reply_markup=markup)
    bot.register_next_step_handler(msg, ask_rank, bot)

def ask_rank(message, bot):
    game = message.text
    if game not in ["CS2", "Dota 2", "Valorant"]:
        msg = bot.send_message(message.chat.id, "Пожалуйста, выбери игру из предложенных.")
        bot.register_next_step_handler(msg, ask_rank, bot)
        return
    
    user_data = {'game': game}
    
    if game == "Dota 2":
        msg = bot.send_message(
            message.chat.id, 
            "🏆 Введите ваш MMR (число от 1 до 17000):",
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(msg, process_dota_mmr, bot, user_data)
    elif game == "CS2":
        msg = bot.send_message(
            message.chat.id,
            "🏆 Введите ваш Faceit ELO (число от 1 до 5000):",
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(msg, process_faceit_elo, bot, user_data)
    else:  # Valorant
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in range(0, len(VALORANT_RANKS), 3):
            markup.add(*VALORANT_RANKS[i:i+3])
        msg = bot.send_message(message.chat.id, "🏆 Выберите ваш ранг:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_valorant_rank, bot, user_data)

def process_dota_mmr(message, bot, user_data):
    try:
        mmr = int(message.text)
        if not 1 <= mmr <= 17000:
            raise ValueError
        user_data['rank'] = f"{mmr} MMR"
        ask_dota_roles(bot, message, user_data)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Некорректный MMR. Введите число от 1 до 10000.")
        bot.register_next_step_handler(msg, process_dota_mmr, bot, user_data)

def process_faceit_elo(message, bot, user_data):
    try:
        elo = int(message.text)
        if not 1 <= elo <= 5000:
            raise ValueError
        user_data['rank'] = f"{elo} ELO"
        ask_description(bot, message, user_data)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Некорректный ELO. Введите число от 1 до 3000.")
        bot.register_next_step_handler(msg, process_faceit_elo, bot, user_data)

def process_valorant_rank(message, bot, user_data):
    if message.text not in VALORANT_RANKS:
        msg = bot.send_message(message.chat.id, "Пожалуйста, выберите ранг из списка.")
        bot.register_next_step_handler(msg, process_valorant_rank, bot, user_data)
        return
    
    user_data['rank_group'] = message.text
    
    if message.text in VALORANT_SUBRANKS:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        markup.add(*VALORANT_SUBRANKS[message.text])
        
        msg = bot.send_message(
            message.chat.id,
            f"Вы выбрали {message.text}. Укажите ваш подранг:",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, process_valorant_subrank, bot, user_data)
    else:
        user_data['rank'] = message.text
        ask_description(bot, message, user_data)

def process_valorant_subrank(message, bot, user_data):
    rank_group = user_data['rank_group']
    
    if message.text not in VALORANT_SUBRANKS.get(rank_group, []):
        msg = bot.send_message(
            message.chat.id,
            f"Пожалуйста, выберите подранг {rank_group} из списка."
        )
        bot.register_next_step_handler(msg, process_valorant_subrank, bot, user_data)
        return
    
    user_data['rank'] = f"{rank_group} {message.text}"
    ask_description(bot, message, user_data)

def ask_dota_roles(bot, message, user_data):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*DOTA_ROLES)
    markup.add(types.KeyboardButton("Готово"))
    user_data['roles'] = []
    
    msg = bot.send_message(
        message.chat.id,
        "🛡️ Выберите ваши роли (можно несколько, затем нажмите 'Готово'):",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_dota_roles, bot, user_data)

def process_dota_roles(message, bot, user_data):
    if message.text == "Готово":
        if not user_data['roles']:
            msg = bot.send_message(message.chat.id, "Пожалуйста, выберите хотя бы одну роль.")
            bot.register_next_step_handler(msg, process_dota_roles, bot, user_data)
            return
        ask_description(bot, message, user_data)
    elif message.text in DOTA_ROLES:
        if message.text not in user_data['roles']:
            user_data['roles'].append(message.text)
        msg = bot.send_message(
            message.chat.id,
            f"Выбрано: {', '.join(user_data['roles'])}\nПродолжайте выбирать или нажмите 'Готово'",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(*DOTA_ROLES, "Готово")
        )
        bot.register_next_step_handler(msg, process_dota_roles, bot, user_data)
    else:
        msg = bot.send_message(message.chat.id, "Пожалуйста, выбирайте роли из списка.")
        bot.register_next_step_handler(msg, process_dota_roles, bot, user_data)

def ask_description(bot, message, user_data):
    if 'roles' not in user_data:
        user_data['roles'] = ['Any']
    
    msg = bot.send_message(
        message.chat.id,
        "📝 Напишите кратко о себе (максимум 1000 символов):\n\n"
        "Пример:\n"
        "• Играю вечером\n"
        "• Ищу команду для турниров\n"
        "• Есть микрофон",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, finish_form, bot, user_data)

def finish_form(message, bot, user_data):
    profile_data = {
        'first_name': message.from_user.first_name,
        'username': message.from_user.username,
        'game': user_data['game'],
        'rank': user_data['rank'],
        'roles': user_data.get('roles', ['Any']),
        'description': message.text[:1000] if message.text else "",
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    if save_profile_to_db(message.from_user.id, profile_data, bot):
        bot.send_message(
            message.chat.id,
            f"✅ Анкета сохранена!\n\n{format_profile(profile_data)}",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, "❌ Ошибка при сохранении анкеты")

def setup_form_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "📝 Заполнить анкету")
    def handle_fill_form(message):
        ask_game(bot, message)