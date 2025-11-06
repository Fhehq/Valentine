import aiosqlite
import logging
import asyncio
from typing import Optional

DB_PATH = "users.db"

logger = logging.getLogger(__name__)


class UserManager:
    _instance: Optional['UserManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = DB_PATH):
        if not hasattr(self, '_initialized'):
            self.db_path = db_path
            self._initialized = False
            self._connection: Optional[aiosqlite.Connection] = None

    async def _get_connection(self) -> aiosqlite.Connection:
        """Возвращает единственное соединение с базой"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            await self._connection.execute("PRAGMA journal_mode=WAL")
            logger.info("Создано новое соединение с БД")
        return self._connection

    async def _initialize_db(self):
        """Инициализирует базу данных"""
        async with self._lock:
            if self._initialized:
                return
            
            conn = await self._get_connection()
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    admin INTEGER DEFAULT 0,
                    limits INTEGER DEFAULT 0
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_admin ON users(admin)
            """)
            await conn.commit()
            self._initialized = True
            logger.info("База данных инициализирована")

    async def is_new_user(self, user_id: int) -> bool:
        """Проверяет, новый ли пользователь"""
        await self._initialize_db()
        conn = await self._get_connection()
        async with conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row is None

    async def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь админом"""
        await self._initialize_db()
        conn = await self._get_connection()
        async with conn.execute("SELECT admin FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return bool(row[0]) if row else False

    async def get_users(self) -> list[int]:
        """Возвращает список всех пользователей"""
        await self._initialize_db()
        conn = await self._get_connection()
        async with conn.execute("SELECT id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def add_user(self, user_id: int, admin: bool = False):
        """Добавляет нового пользователя (если его ещё нет)"""
        await self._initialize_db()
        conn = await self._get_connection()
        await conn.execute(
            "INSERT OR IGNORE INTO users (id, admin) VALUES (?, ?)",
            (user_id, int(admin))
        )
        await conn.commit()

    async def add_admin(self, user_id: int):
        """Назначает пользователя админом"""
        await self._initialize_db()
        conn = await self._get_connection()
        await conn.execute(
            "UPDATE users SET admin = 1 WHERE id = ?",
            (user_id,)
        )
        await conn.commit()

    async def remove_admin(self, user_id: int):
        """Снимает права админа"""
        await self._initialize_db()
        conn = await self._get_connection()
        await conn.execute(
            "UPDATE users SET admin = 0 WHERE id = ?",
            (user_id,)
        )
        await conn.commit()
    
    async def get_balance(self, user_id: int) -> int:
        """Проверяет, баланс пользователя"""
        await self._initialize_db()
        conn = await self._get_connection()
        async with conn.execute("SELECT balance FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
        print(row)
        return row[0]
    
    async def get_limits(self, user_id: int, counts: bool = False) -> bool | int:
        """Проверяет, есть ли у пользователя лимиты или возвращает их"""

        await self._initialize_db()
        conn = await self._get_connection()
        async with conn.execute("SELECT limits FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            
        if counts:
            return row[0]
        
        if await self.is_admin(user_id=user_id):
            return True
         
        if row is None:
            return False
        return row[0] < 3
        
    async def increment_limits(self, user_id: int) -> None:
        """Увеличивает счётчик использованных лимитов"""
        try:
            await self._initialize_db()
            conn = await self._get_connection()
            await conn.execute(
                "UPDATE users SET limits = limits + 1 WHERE id = ?",
                (user_id,)
            )
            await conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при увеличении лимитов: {e}")
    
    async def reset_all_limits(self) -> bool:
        """Сбрасывает все лимиты пользователей"""
        try:
            await self._initialize_db()
            conn = await self._get_connection()
            await conn.execute("UPDATE users SET limits = 0")
            await conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка при сбросе лимитов: {e}")
            return False
    
    async def close(self):
        """Закрывает соединение с БД"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._initialized = False
            logger.info("Соединение с БД закрыто")


# Глобальный экземпляр
user_manager = UserManager()