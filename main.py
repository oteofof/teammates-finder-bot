import telebot
import logging
import time
from config import BOT_TOKEN, ADMIN_CHAT_ID
from database import init_db, add_admin, can_report, check_auto_ban

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_handlers(bot):
    try:
        from handlers.start import setup_start_handlers
        from handlers.search import setup_search_handlers
        from handlers.profile import setup_profile_handlers
        from handlers.forms import setup_form_handlers
        from handlers.reports import setup_report_handlers
        
        setup_start_handlers(bot)
        setup_search_handlers(bot)
        setup_profile_handlers(bot)
        setup_form_handlers(bot)
        setup_report_handlers(bot, ADMIN_CHAT_ID)
    except ImportError as e:
        logger.critical(f"Failed to import handlers: {e}")
        raise

def run_bot():
    try:

        init_db()
        add_admin(ADMIN_CHAT_ID)
        
        bot = telebot.TeleBot(BOT_TOKEN)
        setup_handlers(bot)
        
        logger.info("Bot started successfully")
        bot.infinity_polling()
        
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        time.sleep(5)
        run_bot()

if __name__ == '__main__':
    run_bot()