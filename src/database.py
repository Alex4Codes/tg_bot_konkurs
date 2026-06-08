import aiosqlite
from src.config import settings

async def init_db():
    """Инициализация таблиц при запуске"""
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_participant(user_id: int, username: str, full_name: str) -> bool:
    """Добавляет участника. Возвращает True, если добавлен успешно, False если уже был."""
    async with aiosqlite.connect(settings.db_path) as db:
        try:
            await db.execute(
                "INSERT INTO participants (user_id, username, full_name) VALUES (?, ?, ?)",
                (user_id, username, full_name)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            # Пользователь уже есть в базе (PRIMARY KEY constraint)
            return False

async def get_participants_count() -> int:
    """Возвращает общее количество участников (для админа)"""
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM participants")
        result = await cursor.fetchone()
        return result[0] if result else 0
