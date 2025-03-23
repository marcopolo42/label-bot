from label_cog.src.utils import get_discord_url

import aiosqlite

from label_cog.src.logging_dotenv import setup_logger

from label_cog.src.config import Config
logger = setup_logger(__name__)


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.conn = None
        return cls._instance

    async def initialize(self, db_path):
        if self.conn is None:
            self.conn = await aiosqlite.connect(db_path)

    async def execute(self, query, params=None):
        async with self.conn.cursor() as cursor:
            await cursor.execute(query, params)
            await self.conn.commit()
            return cursor

    async def fetchone(self, query, params=None):
        async with self.conn.cursor() as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchone()

    async def fetchall(self, query, params=None):
        async with self.conn.cursor() as cursor:
            await cursor.execute(query, params)
            return await cursor.fetchall()

    async def close(self):
        await self.conn.close()
        self.conn = None


async def create_tables():
    db = Database()
    await db.execute('''CREATE TABLE IF NOT EXISTS logs
                      (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        log TEXT,
                        user_id INTEGER, 
                        user_display_name TEXT,
                        user_avatar_url TEXT,
                        template_key TEXT, 
                        label_count INTEGER,
                        coins INTEGER DEFAULT 0,
                        creation_date TEXT DEFAULT CURRENT_TIMESTAMP
                      )''')
    await db.execute('''CREATE TABLE IF NOT EXISTS users
                        (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            discord_id INTEGER,
                            display_name TEXT,
                            avatar_url TEXT,
                            discord_url TEXT,
                            language TEXT,
                            coins INTEGER DEFAULT 0,
                            creation_date TEXT DEFAULT CURRENT_TIMESTAMP
                        )''')


async def add_log(log, author, label):
    await Database().execute("INSERT INTO logs (log, user_id, user_display_name, user_avatar_url, template_key, label_count) VALUES (?, ?, ?, ?, ?, ?)",
                      (log, author.id, author.display_name, author.avatar.url, label.template.key, label.count))


async def get_logs():
    logs = await Database().fetchall("SELECT * FROM logs")
    str_logs = ""
    for log in logs:
        logger.debug(log)
        logs += log.__str__() + "\n"
    return str_logs


# count the number of label prints today using the user id and the label.count
async def get_today_prints_count(author, template_key):
    count = await Database().fetchone("SELECT SUM(label_count) FROM logs WHERE user_id = ? AND creation_date > datetime('now', '-1 day') AND template_key = ?", (author.id, template_key))
    if count is None or count[0] is None:
        return 0
    return count[0]


async def add_user(author):
    language = Config().get("default_language")
    coins = Config().get("default_coins")
    await Database().execute("INSERT INTO users (discord_id, display_name, avatar_url, discord_url, language, coins) VALUES (?, ?, ?, ?, ?, ?)",
                      (author.id, author.display_name, author.avatar.url, get_discord_url(str(author.id)), language, coins))


async def get_user(author):
    user = await Database().fetchone("SELECT * FROM users WHERE discord_id = ?", (author.id,))
    return user


async def update_user_language(author, language):
    if await get_user(author) is None:
        await add_user(author, language)
        return
    await Database().execute("UPDATE users SET language = ? WHERE discord_id = ?", (language, author.id))


async def get_user_language(author):
    logger.debug(f"DB connection: {Database().conn}")
    language = await Database().fetchone("SELECT language FROM users WHERE discord_id = ?", (author.id,))
    if language is None:
        logger.info("Default language, because user not found in database, now adding user")
        await add_user(author)
        return "en"
    logger.debug(f"Successfully fetched language {language[0]}")
    return language[0]


async def get_user_coins(author):
    coins = await Database().fetchone("SELECT coins FROM users WHERE discord_id = ?", (author.id,))
    if coins is None:
        await add_user(author)  # todo add default language to config
        logger.info("No coins, because user not found in database")
        return 0
    return coins[0]


async def update_user_coins(author, coins):
    await Database().execute("UPDATE users SET coins = ? WHERE discord_id = ?", (coins, author.id))


async def add_user_coins(author, coins):
    user_coins = await get_user_coins(author)
    await update_user_coins(author, user_coins + coins)


async def can_user_afford(author, price):
    user_coins = await get_user_coins(author)
    if user_coins < price:
        return False
    return True


async def spend_user_coins(author, price):
    user_coins = await get_user_coins(author)
    if user_coins < price:
        return False
    else:
        await Database().execute("UPDATE users SET coins = ? WHERE discord_id = ?", (user_coins - price, author.id))
        return True
