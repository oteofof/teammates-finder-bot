import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect('teammates.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS profiles
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  game TEXT,
                  rank TEXT,
                  roles TEXT,
                  description TEXT,
                  timestamp TEXT,
                  is_banned BOOLEAN DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reports
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  profile_id INTEGER,
                  reporter_id INTEGER,
                  reason TEXT,
                  timestamp TEXT,
                  status TEXT DEFAULT 'pending')''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS admins
                 (user_id INTEGER PRIMARY KEY)''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def can_report(reporter_id, profile_id):
    try:
        conn = sqlite3.connect('teammates.db')
        c = conn.cursor()
        c.execute('''SELECT COUNT(*) FROM reports 
                     WHERE reporter_id = ? AND profile_id = ? 
                     AND timestamp > datetime('now', '-1 day')''',
                  (reporter_id, profile_id))
        count = c.fetchone()[0]
        return count < 3 
    except Exception as e:
        logger.error(f"Error in can_report: {e}")
        return False
    finally:
        conn.close()

def check_auto_ban(profile_id):
    try:
        conn = sqlite3.connect('teammates.db')
        c = conn.cursor()
        c.execute('''SELECT COUNT(*) FROM reports 
                     WHERE profile_id = ? AND status = 'pending' ''',
                  (profile_id,))
        count = c.fetchone()[0]
        if count >= 5:  
            ban_profile(profile_id)
    except Exception as e:
        logger.error(f"Error in check_auto_ban: {e}")
    finally:
        conn.close()


def save_profile_to_db(user_id, user_data, bot):
    try:
        
        init_db()
        
        user = bot.get_chat(user_id)
        conn = sqlite3.connect('teammates.db')
        c = conn.cursor()
        
        c.execute('''INSERT OR REPLACE INTO profiles 
             (user_id, username, first_name, nickname, gender, game, rank, roles, description, timestamp)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
          (user_id,
           user.username if user.username else "",
           user.first_name if user.first_name else "",
           user_data.get('nickname', ''),
           user_data.get('gender', ''),
           user_data.get('game'),
                   user_data.get('rank'),
                   ",".join(user_data.get('roles', [])) if isinstance(user_data.get('roles'), list) else user_data.get('roles', ''),
                   user_data.get('description', ''),
                   datetime.now().strftime("%Y-%m-%d %H:%M")))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database save error: {e}")
        return False


def get_profile_from_db(user_id):
    """Получение профиля из базы данных"""
    try:
        conn = sqlite3.connect('teammates.db')
        c = conn.cursor()
        
        c.execute('''SELECT username, first_name, game, rank, roles, description, timestamp 
                     FROM profiles WHERE user_id = ? AND is_banned = 0''', (user_id,))
        result = c.fetchone()
        
        conn.close()
        
        if result:
            return {
                'username': result[0],
                'first_name': result[1],
                'game': result[2],
                'rank': result[3],
                'roles': result[4].split(",") if result[4] else [],
                'description': result[5],
                'timestamp': result[6]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting profile from DB: {e}")
        return None

def search_profiles_in_db(game=None, min_rank=None, max_rank=None, roles=None, limit=5, exclude_user_id=None):
    """Поиск профилей с фильтрами"""
    try:
        conn = sqlite3.connect('teammates.db')
        c = conn.cursor()
        
        query = '''SELECT user_id, username, first_name, nickname, gender, game, rank, roles, description, timestamp 
                   FROM profiles WHERE is_banned = 0 AND user_id != ?'''
        params = [exclude_user_id or 0]
        
        conditions = []
        if game:
            conditions.append("game = ?")
            params.append(game)
        
        if min_rank and max_rank:
            conditions.append("(rank BETWEEN ? AND ?)")
            params.extend([min_rank, max_rank])
        
        if roles and isinstance(roles, list):
            roles_condition = " OR ".join(["roles LIKE ?" for _ in roles])
            conditions.append(f"({roles_condition})")
            params.extend([f"%{role}%" for role in roles])
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        c.execute(query, params)
        results = c.fetchall()
        
        conn.close()
        
        return [{
            'user_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'nickname': row[3],
            'gender': row[4],
            'game': row[5],
            'rank': row[6],
            'roles': row[7].split(",") if row[7] else [],
            'description': row[8],
            'timestamp': row[9]
        } for row in results]
    except Exception as e:
        logger.error(f"Error searching profiles in DB: {e}")
        return []


def add_report(profile_id, reporter_id, reason):
    """Добавление жалобы в базу данных"""
    try:
        conn = sqlite3.connect('teammates.db')
        c = conn.cursor()
        c.execute('''INSERT INTO reports 
                     (profile_id, reporter_id, reason, timestamp)
                     VALUES (?, ?, ?, ?)''',
                  (profile_id, reporter_id, reason, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error adding report: {e}")
        return False

def get_pending_reports():
    """Получение необработанных жалоб"""
    try:
        conn = sqlite3.connect('teammates.db')
        c = conn.cursor()
        c.execute('''SELECT r.id, p.user_id, p.username, p.first_name, 
                            r.reason, r.timestamp, r.reporter_id
                     FROM reports r
                     JOIN profiles p ON r.profile_id = p.user_id
                     WHERE r.status = 'pending' AND p.is_banned = 0''')
        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error getting pending reports: {e}")
        return []

def ban_profile(profile_id):
    try:
        conn = sqlite3.connect('teammates.db')
        c = conn.cursor()
        c.execute("UPDATE profiles SET is_banned = 1 WHERE user_id = ?", (profile_id,))
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        logger.error(f"Error in ban_profile: {e}")
        return False
    finally:
        conn.close()


def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    try:
        conn = sqlite3.connect('teammates.db')
        c = conn.cursor()
        c.execute('''SELECT 1 FROM admins WHERE user_id = ?''', (user_id,))
        result = c.fetchone()
        conn.close()
        return bool(result)
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

def add_admin(user_id):
    """Добавление администратора"""
    try:
        conn = sqlite3.connect('teammates.db')
        c = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO admins (user_id) VALUES (?)''', (user_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        return False

def migrate_db():
    try:
        conn = sqlite3.connect('teammates.db')
        c = conn.cursor()

        c.execute("PRAGMA table_info(profiles)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'nickname' not in columns:
            c.execute("ALTER TABLE profiles ADD COLUMN nickname TEXT DEFAULT ''")
        if 'gender' not in columns:
            c.execute("ALTER TABLE profiles ADD COLUMN gender TEXT DEFAULT ''")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False

init_db()
migrate_db()
