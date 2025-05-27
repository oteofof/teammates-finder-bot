from main import logger
from telebot import types
from database import search_profiles_in_db, get_profile_from_db
from utils.formatters import format_search_result

def show_search_results(bot, chat_id, profiles):
    if not profiles:
        bot.send_message(chat_id, "😞 Никого не найдено. Попробуйте изменить фильтры.")
        return
    
    for profile in profiles[:5]:
        try:
            markup = types.InlineKeyboardMarkup(row_width=2)
            contact_btn = types.InlineKeyboardButton(
                "📨 Написать", 
                url=f"tg://user?id={profile['user_id']}"
            )
            report_btn = types.InlineKeyboardButton(
                "⚠️ Пожаловаться", 
                callback_data=f"report_{profile['user_id']}"
            )
            markup.add(contact_btn, report_btn)
            
            bot.send_message(
                chat_id,
                format_search_result(profile),
                parse_mode="Markdown",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Error showing profile {profile['user_id']}: {e}")
    
    if len(profiles) > 5:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            text="Показать ещё",
            callback_data=f"more_results:{len(profiles)}"
        ))
        bot.send_message(
            chat_id,
            f"Найдено {len(profiles)} анкет. Показаны первые 5.",
            reply_markup=markup
        )

def show_search_menu(bot, message):
    """Главное меню поиска"""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        "🎮 Dota 2", 
        "🔫 CS2", 
        "💥 Valorant",
        "↩️ На главную"
    ]

    markup.add(*buttons)
    bot.send_message(message.chat.id, "Выберите вариант поиска:", reply_markup=markup)

def search_by_current_game(bot, message):
    """Поиск по текущей игре пользователя"""
    profile = get_profile_from_db(message.from_user.id)
    if not profile:
        bot.send_message(message.chat.id, "❌ Сначала заполните анкету!")
        return
    
    filters = {
        'game': profile['game'],
        'exclude_user_id': message.from_user.id
    }
    
    # Для Dota 2 добавляем фильтр по ролям
    if profile['game'] == 'Dota 2' and profile.get('roles'):
        filters['roles'] = profile['roles']
    
    results = search_profiles_in_db(**filters)
    show_search_results(bot, message.chat.id, results)

def setup_search_handlers(bot):
    @bot.message_handler(func=lambda m: m.text in ["🎮 Dota 2", "🔫 CS2", "💥 Valorant"])
    def handle_game_search(message):
        game_map = {
            "🎮 Dota 2": "Dota 2",
            "🔫 CS2": "CS2",
            "💥 Valorant": "Valorant"
        }
        results = search_profiles_in_db(
            game=game_map[message.text],
            exclude_user_id=message.from_user.id
        )
        show_search_results(bot, message.chat.id, results)