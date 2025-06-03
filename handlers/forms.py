from telebot import types
from datetime import datetime
from config import GENDERS, VALORANT_RANKS, VALORANT_SUBRANKS, DOTA_ROLES
from database import save_profile_to_db
from utils.formatters import format_profile
from utils.validators import is_valid_dota_mmr, is_valid_faceit_elo

def ask_game(bot, message):
    msg = bot.send_message(
        message.chat.id,
        "🎮 Введите ваш игровой ник (макс. 25 символов):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, ask_gender, bot)

def ask_gender(message, bot):
    if len(message.text) > 25:
        msg = bot.send_message(message.chat.id, "❌ Слишком длинный ник! Максимум 25 символов.")
        bot.register_next_step_handler(msg, ask_gender, bot)
        return

    user_data = {'nickname': message.text.strip()}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(*[types.KeyboardButton(gender) for gender in GENDERS])
    
    msg = bot.send_message(
        message.chat.id,
        "👫 Укажите ваш пол:",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_gender, bot, user_data)

def process_gender(message, bot, user_data):
    if message.text not in GENDERS:
        msg = bot.send_message(message.chat.id, "Пожалуйста, выберите пол из предложенных.")
        bot.register_next_step_handler(msg, process_gender, bot, user_data)
        return
    
    user_data['gender'] = message.text
    
    # Переходим к выбору игры
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_cs = types.KeyboardButton("CS2")
    btn_dota = types.KeyboardButton("Dota 2")
    btn_valorant = types.KeyboardButton("Valorant")
    markup.add(btn_cs, btn_dota, btn_valorant)
    
    msg = bot.send_message(message.chat.id, "🎮 Выбери игру:", reply_markup=markup)
    bot.register_next_step_handler(msg, ask_rank, bot, user_data)

def ask_rank(message, bot, user_data):
    game = message.text
    if game not in ["CS2", "Dota 2", "Valorant"]:
        msg = bot.send_message(message.chat.id, "Пожалуйста, выбери игру из предложенных.")
        bot.register_next_step_handler(msg, ask_rank, bot, user_data)
        return
    
    user_data['game'] = game
    
    if game == "Dota 2":
        msg = bot.send_message(
            message.chat.id, 
            "🏆 Введите ваш MMR (число от 50 до 17000):",
            reply_markup=types.ReplyKeyboardRemove()
        )
        bot.register_next_step_handler(msg, process_dota_mmr, bot, user_data)
    elif game == "CS2":
        msg = bot.send_message(
            message.chat.id,
            "🏆 Введите ваш Faceit ELO (число от 100 до 5000):",
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
    """Обработка MMR для Dota 2"""
    try:
        mmr = int(message.text)
        if not is_valid_dota_mmr(message.text):
            raise ValueError
        user_data['rank'] = f"{mmr} MMR"
        ask_dota_roles(bot, message, user_data)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Некорректный MMR. Введите число от 50 до 17000.")
        bot.register_next_step_handler(msg, process_dota_mmr, bot, user_data)

def process_faceit_elo(message, bot, user_data):
    """Обработка ELO для CS2"""
    try:
        elo = int(message.text)
        if not is_valid_faceit_elo(message.text):
            raise ValueError
        user_data['rank'] = f"{elo} ELO"
        ask_description(bot, message, user_data)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Некорректный ELO. Введите число от 100 до 5000.")
        bot.register_next_step_handler(msg, process_faceit_elo, bot, user_data)

def process_valorant_rank(message, bot, user_data):
    """Обработка ранга для Valorant"""
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
    """Обработка подранга для Valorant"""
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
    """Запрос ролей для Dota 2"""
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
    """Обработка выбранных ролей для Dota 2"""
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
    """Запрос описания профиля"""
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

from handlers.start import start

def finish_form(message, bot, user_data):
    """Завершение анкеты и сохранение"""
    profile_data = {
        'first_name': message.from_user.first_name,
        'username': message.from_user.username,
        'nickname': user_data.get('nickname', ''),
        'gender': user_data.get('gender', ''),
        'game': user_data['game'],
        'rank': user_data['rank'],
        'roles': user_data.get('roles', ['Any']),
        'description': message.text[:1000] if message.text else "",
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    if save_profile_to_db(message.from_user.id, profile_data, bot):
        success_message = (
            "✅ Анкета сохранена!\n\n"
            f"{format_profile(profile_data)}"
        )
        
        # Сначала отправляем сообщение о сохранении
        bot.send_message(
            message.chat.id,
            success_message,
            parse_mode=None
        )
        
        # Затем показываем главное меню
        from handlers.start import setup_start_handlers  # Импортируем функцию start
        start(message)  # Вызываем функцию start с объектом message
        
    else:
        bot.send_message(message.chat.id, "❌ Ошибка при сохранении анкеты")

def setup_form_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "📝 Заполнить анкету")
    def handle_fill_form(message):
        ask_game(bot, message)
