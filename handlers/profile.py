from telebot import types
from database import get_profile_from_db
from utils.formatters import format_profile

def show_profile(bot, message):
    user_id = message.from_user.id
    profile_data = get_profile_from_db(user_id)
    
    if profile_data:
        profile_text = format_profile(profile_data)
        bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, 
                        "У вас нет сохранённой анкеты. Нажмите '📝 Заполнить анкету' чтобы создать её.",
                        reply_markup=types.ReplyKeyboardRemove())

def setup_profile_handlers(bot):
    @bot.message_handler(func=lambda m: m.text == "👤 Моя анкета")
    def handle_my_profile(message):
        show_profile(bot, message)