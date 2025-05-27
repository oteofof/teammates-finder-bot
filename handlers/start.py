from telebot import types

# Делаем bot глобальной переменной для этого модуля
bot_instance = None

def start(message):
    """Функция для отображения главного меню, которую можно вызывать из других модулей"""
    user = message.from_user
    welcome_text = (
        f"Привет, {user.first_name}! 👋\n"
        "Я помогу найти тиммейтов для игр.\n\n"
        "Доступные команды:\n"
        "📝 Заполнить анкету - создать/обновить свою анкету\n"
        "🔍 Найти игроков - найти подходящих тиммейтов\n"
        "👤 Моя анкета - просмотреть свою анкету\n"
        "🔤 /start - запустить/перезапустить бота\n\n"
        "Используй кнопки ниже для навигации:"
    )
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_fill = types.KeyboardButton("📝 Заполнить анкету")
    btn_search = types.KeyboardButton("🔍 Найти игроков")
    btn_my_profile = types.KeyboardButton("👤 Моя анкета")
    markup.add(btn_fill, btn_search, btn_my_profile)
    
    bot_instance.send_message(message.chat.id, welcome_text, reply_markup=markup)

def setup_start_handlers(bot):
    """Настройка обработчиков команд стартового меню"""
    global bot_instance
    bot_instance = bot  # Сохраняем экземпляр бота для использования в функции start()

    @bot.message_handler(commands=['start', 'help'])
    def handle_start(message):
        start(message)

    @bot.message_handler(func=lambda m: m.text == "👤 Моя анкета")
    def handle_my_profile(message):
        from handlers.profile import show_profile
        show_profile(bot, message)

    @bot.message_handler(func=lambda m: m.text == "🔍 Найти игроков")
    def handle_search(message):
        from handlers.search import show_search_menu
        show_search_menu(bot, message)

    @bot.message_handler(func=lambda m: m.text == "↩️ На главную")
    def handle_back(message):
        start(message)