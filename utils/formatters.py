from telebot import types
from datetime import datetime

def format_profile(profile_data):
    """
    Форматирует данные профиля для отображения в новом стиле
    """
    # Основные поля
    username = profile_data.get('username', 'нет username')
    nickname = profile_data.get('nickname', '')
    first_name = profile_data.get('first_name', 'Игрок')
    
    # Формируем текст профиля
    profile_text = (
        f"👤 {nickname} (@{username})\n\n"
        f"👫 Пол: {profile_data.get('gender', 'Не указан')}\n"
        f"🎮 Игра: {profile_data.get('game', 'Не указана')}\n"
        f"🏆 Ранг: {profile_data.get('rank', 'Не указан')}\n"
        f"📝 О себе: {profile_data.get('description', 'Нет описания')}\n\n"
        f"🕒 Обновлено: {profile_data.get('timestamp', 'Дата не указана')}"
    )
    
    # Если есть роли (для Dota 2)
    roles = profile_data.get('roles', [])
    if roles and roles != ['Any']:
        if isinstance(roles, str):
            roles = [roles]  # На случай, если роли пришли строкой
        profile_text = profile_text.replace(
            "🏆 Ранг:", 
            f"🏆 Ранг: {profile_data.get('rank', 'Не указан')}\n"
            f"🛡 Роли: {', '.join(roles)}"
        )
    
    return profile_text

def format_search_result(profile):
    """
    Форматирует профиль для результатов поиска
    """
    roles_text = ""
    if profile.get('roles') and profile['roles'] != ['Any']:
        roles_text = f"\n🛡️ *Роли:* {', '.join(profile['roles'])}"
    
    return f"""*{profile.get('first_name', 'Игрок')}* (@{profile.get('username', 'нет username')})
🎮 *Игра:* {profile.get('game', '')}
🏆 *Ранг:* {profile.get('rank', '')}{roles_text}
📝 *О себе:* {profile.get('description', '')[:100]}..."""