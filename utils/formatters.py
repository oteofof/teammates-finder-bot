from telebot import types
from datetime import datetime

def format_profile(profile_data):
    username = profile_data.get('username', 'нет username')
    first_name = profile_data.get('first_name', 'Игрок')
    
    profile_text = (
        f"👤 *{first_name}* (@{username})\n\n"
        f"🎮 *Игра:* {profile_data.get('game', 'Не указана')}\n"
        f"🏆 *Ранг:* {profile_data.get('rank', 'Не указан')}\n"
    )
    
    roles = profile_data.get('roles', [])
    if roles and roles != ['Any']:
        if isinstance(roles, str):
            roles = [roles]
        profile_text += f"🛡️ *Роли:* {', '.join(roles)}\n"
    
    description = profile_data.get('description', 'Нет описания')
    timestamp = profile_data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    profile_text += (
        f"📝 *О себе:* {description}\n"
        f"🕒 *Обновлено:* {timestamp}"
    )
    
    return profile_text

def format_search_result(profile):
    roles_text = ""
    if profile.get('roles') and profile['roles'] != ['Any']:
        roles_text = f"\n🛡️ *Роли:* {', '.join(profile['roles'])}"
    
    return f"""*{profile.get('first_name', 'Игрок')}* (@{profile.get('username', 'нет username')})
🎮 *Игра:* {profile.get('game', '')}
🏆 *Ранг:* {profile.get('rank', '')}{roles_text}
📝 *О себе:* {profile.get('description', '')[:100]}..."""