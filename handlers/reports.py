import sqlite3
from telebot import types
import logging
from database import (add_report, get_pending_reports, ban_profile, 
                     is_admin, can_report, check_auto_ban)

logger = logging.getLogger(__name__)

def setup_report_handlers(bot, admin_chat_id):
    @bot.callback_query_handler(func=lambda call: call.data.startswith('report_'))
    def handle_report_callback(call):
        try:
            profile_id = int(call.data.split('_')[1])
            
            if not can_report(call.from_user.id, profile_id):
                bot.answer_callback_query(
                    call.id,
                    "❌ Вы уже жаловались на этого пользователя сегодня",
                    show_alert=True
                )
                return
                
            msg = bot.send_message(
                call.message.chat.id,
                "📝 Опишите причину жалобы (максимум 500 символов):",
                reply_markup=types.ForceReply(selective=True)
            )
            bot.register_next_step_handler(
                msg, 
                lambda m: process_report_reason(bot, m, profile_id, call.from_user.id, admin_chat_id)
            )
        except Exception as e:
            logger.error(f"Error in handle_report_callback: {e}")

    def process_report_reason(bot, message, profile_id, reporter_id, admin_chat_id):
        try:
            reason = message.text[:500]
            if add_report(profile_id, reporter_id, reason):
                bot.send_message(
                    message.chat.id,
                    "✅ Ваша жалоба отправлена администратору",
                    reply_markup=types.ReplyKeyboardRemove()
                )
                check_auto_ban(profile_id)
                notify_admin(bot, admin_chat_id, profile_id, reason, reporter_id)
            else:
                bot.send_message(message.chat.id, "❌ Ошибка при отправке жалобы")
        except Exception as e:
            logger.error(f"Error in process_report_reason: {e}")

    def notify_admin(bot, admin_chat_id, profile_id, reason, reporter_id):
        try:
            bot.send_message(
        admin_chat_id,
        f"⚠️ Новая жалоба!\n\n"
        f"👤 На пользователя: #{profile_id}\n"
        f"🖊 От пользователя: #{reporter_id}\n"
        f"📝 Причина: {reason}\n\n"
        f"Для модерации используйте команду /moderate"
)

        except Exception as e:
            logger.error(f"Error in notify_admin: {e}")

    @bot.message_handler(commands=['moderate'])
    def handle_moderate_command(message):
        try:
            if not is_admin(message.from_user.id):
                bot.send_message(message.chat.id, "❌ Эта команда только для администраторов")
                return
                
            reports = get_pending_reports()
            if not reports:
                bot.send_message(message.chat.id, "✅ Нет активных жалоб")
                return
                
            for report in reports:
                show_report(bot, message.chat.id, report)
        except Exception as e:
            logger.error(f"Error in handle_moderate_command: {e}")

    def show_report(bot, chat_id, report):
        try:
            report_id, profile_id, username, first_name, reason, timestamp, reporter_id = report
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("⛔ Забанить", callback_data=f"ban_{profile_id}"),
                types.InlineKeyboardButton("✅ Отклонить", callback_data=f"reject_{report_id}")
            )
            
            bot.send_message(
                chat_id,
                f"🛡 Жалоба #{report_id}\n\n"
                f"👤 Пользователь: {first_name} (@{username if username else 'нет'})\n"
                f"🆔 ID: {profile_id}\n"
                f"📝 Причина: {reason}\n"
                f"⏰ Дата: {timestamp}\n"
                f"👁‍🗨 Отправил: {reporter_id}",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Error in show_report: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('ban_'))
    def handle_ban(call):
        try:
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ Только для администраторов", show_alert=True)
                return
                
            profile_id = int(call.data.split('_')[1])
            if ban_profile(profile_id):
                bot.answer_callback_query(call.id, "✅ Пользователь забанен")
                bot.edit_message_text(
                    f"⛔ Пользователь #{profile_id} забанен",
                    call.message.chat.id,
                    call.message.message_id
                )
            else:
                bot.answer_callback_query(call.id, "❌ Ошибка при бане пользователя")
        except Exception as e:
            logger.error(f"Error in handle_ban: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('reject_'))
    def handle_reject(call):
        try:
            if not is_admin(call.from_user.id):
                bot.answer_callback_query(call.id, "❌ Только для администраторов", show_alert=True)
                return
                
            report_id = int(call.data.split('_')[1])
            
            # Исправленная часть с использованием sqlite3
            conn = sqlite3.connect('teammates.db')
            c = conn.cursor()
            c.execute("UPDATE reports SET status = 'rejected' WHERE id = ?", (report_id,))
            conn.commit()
            conn.close()
            
            bot.answer_callback_query(call.id, "✅ Жалоба отклонена")
            bot.edit_message_text(
                f"✅ Жалоба #{report_id} отклонена",
                call.message.chat.id,
                call.message.message_id
            )
        except Exception as e:
            logger.error(f"Error in handle_reject: {e}")