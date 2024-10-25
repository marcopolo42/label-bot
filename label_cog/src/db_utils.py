import sqlite3
from label_cog.src.utils import get_discord_url


def create_tables():
    conn = sqlite3.connect('label_cog/database.sqlite')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs
                      (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        log TEXT,
                        user_id INTEGER, 
                        user_display_name TEXT,
                        user_avatar_url TEXT,
                        template_key TEXT, 
                        label_count INTEGER, 
                        creation_date TEXT DEFAULT CURRENT_TIMESTAMP
                      )''')
    #for future language and TIG feature support
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                        (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            discord_id INTEGER,
                            display_name TEXT,
                            avatar_url TEXT,
                            discord_url TEXT,
                            language TEXT,
                            creation_date TEXT DEFAULT CURRENT_TIMESTAMP

                        )''')
    conn.commit()
    conn.close()


def add_log(log, author, label, conn):
    cursor = conn.cursor()
    if label.template is None:
        cursor.execute("INSERT INTO logs (log, user_id, user_display_name, user_avatar_url) VALUES (?, ?, ?, ?)",
                       (log, author.id, author.display_name, author.avatar.url))
    else:
        cursor.execute(
            "INSERT INTO logs (log, user_id, user_display_name, user_avatar_url, template_key, label_count) VALUES (?, ?, ?, ?, ?, ?)",
            (log, author.id, author.display_name, author.avatar.url, label.template.key, label.count))
    conn.commit()


def get_logs(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs")
    rows = cursor.fetchall()
    logs = ""
    for row in rows:
        print(row)
        logs += row.__str__() + "\n"
    return logs


# count the number of label prints today using the user id and the label.count
def get_today_prints_count(author, template_key, conn):
    cursor = conn.cursor()
    # select the sum of label_count from logs where the user_id is the same as the author's id and the creation date is in the last 24 hours and the label_type is the same as the label_type
    cursor.execute(
        "SELECT SUM(label_count) FROM logs WHERE user_id = ? AND creation_date > datetime('now', '-1 day') AND template_key = ?", (author.id, template_key))
    count = cursor.fetchone()
    if count is None:
        return 0
    if count[0] is None:
        return 0
    return count[0]


# add a user to the database
def add_user(author, language, conn):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (discord_id, display_name, avatar_url, discord_url, language) VALUES (?, ?, ?, ?, ?)",
                   (author.id, author.display_name, author.avatar.url, get_discord_url(author.id), language))
    conn.commit()


def get_user(author, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE discord_id = ?", (author.id,))
    user = cursor.fetchone()
    return user


def update_user_language(author, language, conn):
    if get_user(author, conn) is None:
        add_user(author, language, conn)
        return
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE discord_id = ?", (language, author.id))
    conn.commit()


def get_user_language(author, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE discord_id = ?", (author.id,))
    language = cursor.fetchone()
    if language is None:
        print("Default language, because user not found in database")
        return "en"
    return language[0]
